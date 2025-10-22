import os
import logging
from typing import List, Dict, Any
from celery import shared_task
from datetime import datetime

from extensions import db
from models.image import Image
from models.modern_image import ModernImage
from models.user import User
from services.image_service import ImageService
from services.modern_image_service import ModernImageService
from services.email_service import EmailService
from utils.helpers import validate_and_process_image, create_directory_structure
from utils.security import generate_secure_filename, calculate_file_hash
from middleware.audit_logger import AuditLogger
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_async(self, image_id: int, extract_text: bool = True,
                       detect_faces: bool = True, generate_embeddings: bool = True):
    """
    Process an image with configurable options.

    Args:
        image_id: ID of the image to process
        extract_text: Whether to extract text from the image using OCR
        detect_faces: Whether to detect and process faces in the image
        generate_embeddings: Whether to generate vector embeddings for similarity search
    """
    try:
        # Try ModernImage first (v2 API), fall back to Image (v1 API)
        image = ModernImage.query.get(image_id)
        use_modern = True

        if not image:
            image = Image.query.get(image_id)
            use_modern = False

        if not image:
            logger.error(f"Image with ID {image_id} not found in any table")
            return {'success': False, 'error': 'Image not found'}

        logger.info(f"Starting processing for image {image_id} (text={extract_text}, faces={detect_faces}, embeddings={generate_embeddings}, modern={use_modern})")

        if use_modern:
            # Use modern service for v2 images
            image_service = ModernImageService()
            success = image_service.process_image_content(
                image=image,
                extract_text=extract_text,
                detect_faces=detect_faces,
                generate_embeddings=generate_embeddings
            )
        else:
            # Use legacy service for v1 images
            image_service = ImageService()
            success = image_service.process_single_image(
                image_id=image_id,
                extract_text=extract_text,
                detect_faces=detect_faces,
                generate_embeddings=generate_embeddings
            )

        if success:
            logger.info(f"Successfully processed image {image_id}")
            return {
                'success': True,
                'image_id': image_id,
                'message': 'Image processed successfully'
            }
        else:
            error_msg = image.processing_error if hasattr(image, 'processing_error') else 'Unknown processing error'
            logger.error(f"Failed to process image {image_id}: {error_msg}")
            return {
                'success': False,
                'image_id': image_id,
                'error': error_msg
            }

    except Exception as e:
        logger.error(f"Image processing task failed for ID {image_id}: {str(e)}")

        try:
            image = ModernImage.query.get(image_id) or Image.query.get(image_id)
            if image and hasattr(image, 'fail_processing'):
                image.fail_processing(f"Task error: {str(e)}")
            elif image and hasattr(image, 'mark_processing_failed'):
                image.mark_processing_failed(f"Task error: {str(e)}")
        except Exception:
            pass

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying image processing for ID {image_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            'success': False,
            'image_id': image_id,
            'error': str(e),
            'retries_exhausted': True
        }

@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def batch_process_images_async(self, user_id: int, file_data_list: List[Dict[str, Any]]):
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return {'success': False, 'error': 'User not found'}
        
        logger.info(f"Starting batch processing for user {user_id} with {len(file_data_list)} files")
        
        image_service = ImageService()
        email_service = EmailService()
        
        upload_paths = image_service.create_user_directories(user_id)
        
        results = {
            'user_id': user_id,
            'total_files': len(file_data_list),
            'successful_uploads': [],
            'failed_uploads': [],
            'processing_started': [],
            'start_time': datetime.utcnow().isoformat()
        }
        
        for file_info in file_data_list:
            try:
                filename = file_info.get('filename', 'unknown')
                file_data = file_info.get('data')
                content_type = file_info.get('content_type', 'application/octet-stream')
                
                if not file_data:
                    results['failed_uploads'].append({
                        'filename': filename,
                        'error': 'No file data provided'
                    })
                    continue
                
                if isinstance(file_data, str):
                    file_data = file_data.encode()
                
                checksum = calculate_file_hash(file_data)
                existing_image = Image.get_by_checksum(checksum, user_id)
                
                if existing_image:
                    results['failed_uploads'].append({
                        'filename': filename,
                        'error': 'Duplicate image already exists',
                        'existing_image_id': existing_image.id
                    })
                    continue
                
                try:
                    processed_data = validate_and_process_image(file_data, filename)
                    
                    secure_filename = generate_secure_filename(filename)
                    image_path = os.path.join(upload_paths['images'], secure_filename)
                    thumbnail_filename = f"thumb_{secure_filename}"
                    thumbnail_path = os.path.join(upload_paths['thumbnails'], thumbnail_filename)
                    
                    with open(image_path, 'wb') as f:
                        f.write(file_data)
                    
                    with open(thumbnail_path, 'wb') as f:
                        f.write(processed_data['thumbnail_data'])
                    
                    image = Image(
                        filename=secure_filename,
                        original_filename=filename,
                        file_path=image_path,
                        thumbnail_path=thumbnail_path,
                        file_size=processed_data['file_size'],
                        mime_type=content_type,
                        width=processed_data['width'],
                        height=processed_data['height'],
                        checksum=processed_data['checksum'],
                        image_date=processed_data['image_date'],
                        location=processed_data['location_data']['address'] if processed_data['location_data'] else None,
                        exif_data=processed_data['exif_data'],
                        metadata={
                            'location_data': processed_data['location_data'],
                            'latitude': processed_data['latitude'],
                            'longitude': processed_data['longitude']
                        },
                        user_id=user_id
                    )
                    
                    db.session.add(image)
                    db.session.commit()
                    
                    process_image_async.delay(image.id)
                    
                    results['successful_uploads'].append({
                        'image_id': image.id,
                        'filename': filename,
                        'secure_filename': secure_filename
                    })
                    
                    results['processing_started'].append(image.id)
                    
                    AuditLogger.log_image_upload(
                        user_id=user_id,
                        image_id=image.id,
                        filename=filename,
                        ip_address='batch_process',
                        success=True
                    )
                    
                except Exception as processing_error:
                    results['failed_uploads'].append({
                        'filename': filename,
                        'error': f'Processing failed: {str(processing_error)}'
                    })
                    continue
                    
            except Exception as file_error:
                results['failed_uploads'].append({
                    'filename': file_info.get('filename', 'unknown'),
                    'error': str(file_error)
                })
        
        results['end_time'] = datetime.utcnow().isoformat()
        results['success_count'] = len(results['successful_uploads'])
        results['failure_count'] = len(results['failed_uploads'])
        results['processing_count'] = len(results['processing_started'])
        
        try:
            if results['success_count'] > 0:
                email_service.send_processing_complete_email(
                    user_email=user.email,
                    user_name=user.name,
                    processing_results={
                        'images_processed': results['success_count'],
                        'faces_detected': 'Processing...',
                        'processing_time': 'In progress'
                    }
                )
            
            if results['failure_count'] > 0:
                email_service.send_processing_failed_email(
                    user_email=user.email,
                    user_name=user.name,
                    error_details={
                        'failed_count': results['failure_count'],
                        'error_message': 'Multiple processing errors occurred'
                    }
                )
        except Exception as email_error:
            logger.warning(f"Failed to send notification email: {str(email_error)}")
        
        logger.info(f"Batch processing completed for user {user_id}: {results['success_count']} successful, {results['failure_count']} failed")
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Batch processing task failed for user {user_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch processing for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))
        
        try:
            user = User.query.get(user_id)
            if user:
                email_service = EmailService()
                email_service.send_processing_failed_email(
                    user_email=user.email,
                    user_name=user.name,
                    error_details={
                        'failed_count': len(file_data_list),
                        'error_message': str(e)
                    }
                )
        except Exception:
            pass
        
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e),
            'retries_exhausted': True
        }

@shared_task
def reprocess_failed_images(user_id: int = None, limit: int = 10):
    try:
        logger.info(f"Starting reprocessing of failed images for user {user_id or 'all users'}")
        
        image_service = ImageService()
        results = image_service.reprocess_failed_images(user_id, limit)
        
        logger.info(f"Reprocessing completed: {len(results['reprocessed'])} successful, {len(results['still_failed'])} still failed")
        
        return {
            'success': True,
            'reprocessed_count': len(results['reprocessed']),
            'still_failed_count': len(results['still_failed']),
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Reprocess failed images task error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def cleanup_processing_queue():
    try:
        logger.info("Starting processing queue cleanup")
        
        stuck_processing_images = Image.query.filter(
            Image.status == 'processing',
            Image.processing_started_at < datetime.utcnow() - timedelta(hours=2)
        ).all()
        
        reset_count = 0
        for image in stuck_processing_images:
            image.status = 'pending'
            image.processing_started_at = None
            image.processing_error = 'Reset due to timeout'
            reset_count += 1
        
        db.session.commit()
        
        logger.info(f"Reset {reset_count} stuck processing images")
        
        return {
            'success': True,
            'reset_count': reset_count
        }
    
    except Exception as e:
        logger.error(f"Processing queue cleanup error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def generate_user_processing_report(user_id: int):
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        image_service = ImageService()
        stats = image_service.get_user_image_stats(user_id)
        
        report_data = {
            'user_name': user.name,
            'user_email': user.email,
            'report_date': datetime.utcnow().isoformat(),
            'statistics': stats,
            'recommendations': []
        }
        
        if stats['processing_rate']['failed'] > 0:
            report_data['recommendations'].append(
                f"You have {stats['processing_rate']['failed']} failed images that may need attention."
            )
        
        if stats['processing_rate']['pending'] > stats['total_images'] * 0.1:
            report_data['recommendations'].append(
                "Consider reducing upload frequency as processing queue is building up."
            )
        
        return {
            'success': True,
            'report': report_data
        }
    
    except Exception as e:
        logger.error(f"Processing report generation error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def optimize_image_storage(user_id: int = None):
    try:
        logger.info(f"Starting storage optimization for user {user_id or 'all users'}")
        
        query = Image.query.filter_by(status='completed')
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        images = query.all()
        optimized_count = 0
        space_saved = 0
        
        for image in images:
            try:
                if os.path.exists(image.file_path):
                    original_size = os.path.getsize(image.file_path)
                    
                    if original_size > 5 * 1024 * 1024:  # Files larger than 5MB
                        with open(image.file_path, 'rb') as f:
                            image_data = f.read()
                        
                        from utils.helpers import optimize_image_for_processing
                        optimized_data = optimize_image_for_processing(image_data, max_dimension=2048)
                        
                        if len(optimized_data) < original_size * 0.8:  # At least 20% savings
                            backup_path = f"{image.file_path}.backup"
                            os.rename(image.file_path, backup_path)
                            
                            with open(image.file_path, 'wb') as f:
                                f.write(optimized_data)
                            
                            new_size = len(optimized_data)
                            space_saved += original_size - new_size
                            optimized_count += 1
                            
                            image.file_size = new_size
                            
                            os.remove(backup_path)
                        
            except Exception as image_error:
                logger.warning(f"Failed to optimize image {image.id}: {str(image_error)}")
                continue
        
        if optimized_count > 0:
            db.session.commit()
        
        logger.info(f"Storage optimization completed: {optimized_count} images optimized, {space_saved} bytes saved")
        
        image_service = ImageService()
        return {
            'success': True,
            'optimized_count': optimized_count,
            'space_saved_bytes': space_saved,
            'space_saved_formatted': image_service.format_file_size(space_saved) if space_saved > 0 else '0 B'
        }
    
    except Exception as e:
        logger.error(f"Storage optimization error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }