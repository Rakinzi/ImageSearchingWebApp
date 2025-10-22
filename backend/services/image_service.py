import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from flask import current_app

from models.image import Image
from services.vector_service import VectorService
from utils.helpers import (
    validate_and_process_image, 
    create_directory_structure,
    format_file_size,
    extract_exif_data,
    extract_gps_coordinates,
    reverse_geocode,
    extract_date_from_exif
)
from utils.security import generate_secure_filename, calculate_file_hash
from extensions import db

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.vector_service = VectorService()
        self.upload_base_path = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure the service is initialized with Flask app context"""
        if not self._initialized:
            self.upload_base_path = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            self._initialized = True
    
    def create_user_directories(self, user_id: int) -> Dict[str, str]:
        self._ensure_initialized()
        try:
            user_paths = create_directory_structure(self.upload_base_path, user_id)
            return user_paths
        except Exception as e:
            logger.error(f"Failed to create user directories: {str(e)}")
            raise Exception(f"Directory creation failed: {str(e)}")
    
    def process_single_image(self, image_id: int, extract_text: bool = True,
                            detect_faces: bool = True, generate_embeddings: bool = True) -> bool:
        """
        Process an image with configurable options.

        Args:
            image_id: ID of the image to process
            extract_text: Whether to extract text from the image using OCR
            detect_faces: Whether to detect and process faces in the image
            generate_embeddings: Whether to generate vector embeddings for similarity search
        """
        try:
            image = Image.query.get(image_id)
            if not image:
                logger.error(f"Image with ID {image_id} not found")
                return False

            if not os.path.exists(image.file_path):
                logger.error(f"Image file not found: {image.file_path}")
                image.mark_processing_failed("Image file not found on disk")
                return False

            image.mark_processing_started()

            with open(image.file_path, 'rb') as f:
                image_data = f.read()

            try:
                # Extract text from image if requested
                if extract_text:
                    logger.info(f"Text extraction requested for image {image_id} (not yet implemented)")
                    # TODO: Implement OCR text extraction
                    # from utils.ocr import extract_text_from_image
                    # extracted_text = extract_text_from_image(image_data)
                    # image.extracted_text = extracted_text

                # Detect faces if requested
                if detect_faces:
                    logger.info(f"Face detection requested for image {image_id} (not yet implemented)")
                    # TODO: Implement face detection
                    # from services.face_service import FaceService
                    # face_service = FaceService()
                    # faces = face_service.detect_faces(image_data, image_id)

                # Generate embeddings if requested
                if generate_embeddings:
                    embedding = self.vector_service.generate_image_embedding(image_data)

                    metadata = {
                        'user_id': image.user_id,
                        'filename': image.filename,
                        'file_path': image.file_path,
                        'mime_type': image.mime_type,
                        'width': image.width,
                        'height': image.height,
                        'file_size': image.file_size,
                        'image_date': image.image_date.isoformat() if image.image_date else None,
                        'location': image.location,
                        'created_at': image.created_at.isoformat()
                    }

                    vector_id = f"img_{image.id}_{image.user_id}"

                    if not self.vector_service.store_image_vector(vector_id, embedding, metadata):
                        image.mark_processing_failed("Failed to store vector embedding")
                        return False

                    image.vector_id = vector_id

                # Mark as completed
                image.mark_processing_completed()
                logger.info(f"Successfully processed image {image_id} (text={extract_text}, faces={detect_faces}, embeddings={generate_embeddings})")
                return True

            except Exception as processing_error:
                error_msg = f"Processing error: {str(processing_error)}"
                image.mark_processing_failed(error_msg)
                logger.error(f"Failed to process image {image_id}: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"Image processing failed for ID {image_id}: {str(e)}")
            return False
    
    def search_images(self, query: str, user_id: int, limit: int = 20, 
                     similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
        try:
            filter_metadata = {'user_id': user_id}
            
            results = self.vector_service.text_to_image_search(
                text_query=query,
                limit=limit,
                similarity_threshold=similarity_threshold,
                filter_metadata=filter_metadata
            )
            
            if not results:
                return []
            
            image_results = []
            for result in results:
                try:
                    vector_id = result['id']
                    image_id = int(vector_id.split('_')[1])
                    
                    image = Image.query.get(image_id)
                    if image and image.user_id == user_id:
                        image_data = {
                            'id': image.id,
                            'similarity_score': result['similarity'],
                            'metadata': result['metadata']
                        }
                        image_results.append(image_data)
                
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid vector ID format: {result['id']}")
                    continue
            
            return image_results
        
        except Exception as e:
            logger.error(f"Image search failed: {str(e)}")
            return []
    
    def find_similar_images(self, image_id: int, user_id: int, 
                          limit: int = 10, similarity_threshold: float = 0.9) -> List[Dict[str, Any]]:
        try:
            image = Image.query.filter_by(id=image_id, user_id=user_id).first()
            if not image or not image.vector_id:
                return []
            
            if not os.path.exists(image.file_path):
                return []
            
            with open(image.file_path, 'rb') as f:
                image_data = f.read()
            
            filter_metadata = {'user_id': user_id}
            
            results = self.vector_service.image_to_image_search(
                image_data=image_data,
                limit=limit + 1,
                similarity_threshold=similarity_threshold,
                filter_metadata=filter_metadata
            )
            
            similar_images = []
            for result in results:
                try:
                    vector_id = result['id']
                    similar_image_id = int(vector_id.split('_')[1])
                    
                    if similar_image_id == image_id:
                        continue
                    
                    similar_image = Image.query.get(similar_image_id)
                    if similar_image and similar_image.user_id == user_id:
                        similar_images.append({
                            'id': similar_image.id,
                            'similarity_score': result['similarity'],
                            'metadata': result['metadata']
                        })
                
                except (ValueError, IndexError):
                    continue
            
            return similar_images[:limit]
        
        except Exception as e:
            logger.error(f"Find similar images failed: {str(e)}")
            return []
    
    def remove_from_vector_db(self, vector_id: str) -> bool:
        try:
            if vector_id:
                return self.vector_service.remove_image_vector(vector_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove vector: {str(e)}")
            return False
    
    def update_image_metadata(self, image_id: int) -> bool:
        try:
            image = Image.query.get(image_id)
            if not image or not image.vector_id:
                return False
            
            metadata = {
                'user_id': image.user_id,
                'filename': image.filename,
                'file_path': image.file_path,
                'mime_type': image.mime_type,
                'width': image.width,
                'height': image.height,
                'file_size': image.file_size,
                'image_date': image.image_date.isoformat() if image.image_date else None,
                'location': image.location,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            return self.vector_service.update_image_metadata(image.vector_id, metadata)
        
        except Exception as e:
            logger.error(f"Failed to update image metadata: {str(e)}")
            return False
    
    def batch_process_images(self, image_ids: List[int]) -> Dict[str, Any]:
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_processed': len(image_ids)
            }
            
            for image_id in image_ids:
                try:
                    if self.process_single_image(image_id):
                        results['successful'].append(image_id)
                    else:
                        results['failed'].append({'id': image_id, 'error': 'Processing failed'})
                except Exception as e:
                    results['failed'].append({'id': image_id, 'error': str(e)})
            
            results['success_count'] = len(results['successful'])
            results['failure_count'] = len(results['failed'])
            
            return results
        
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return {
                'successful': [],
                'failed': [{'error': str(e)}],
                'total_processed': len(image_ids),
                'success_count': 0,
                'failure_count': len(image_ids)
            }
    
    def get_user_image_stats(self, user_id: int) -> Dict[str, Any]:
        try:
            from sqlalchemy import func
            
            total_images = Image.query.filter_by(user_id=user_id).count()
            
            status_stats = db.session.query(
                Image.status,
                func.count(Image.id).label('count')
            ).filter_by(user_id=user_id).group_by(Image.status).all()
            
            total_size = db.session.query(
                func.sum(Image.file_size)
            ).filter_by(user_id=user_id).scalar() or 0
            
            avg_size = db.session.query(
                func.avg(Image.file_size)
            ).filter_by(user_id=user_id).scalar() or 0
            
            recent_uploads = Image.query.filter_by(
                user_id=user_id
            ).filter(
                Image.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            status_breakdown = {status: count for status, count in status_stats}
            
            return {
                'total_images': total_images,
                'total_size_bytes': total_size,
                'total_size_formatted': self.format_file_size(total_size),
                'average_size_bytes': int(avg_size),
                'average_size_formatted': self.format_file_size(int(avg_size)),
                'recent_uploads_today': recent_uploads,
                'status_breakdown': status_breakdown,
                'processing_rate': {
                    'completed': status_breakdown.get('completed', 0),
                    'pending': status_breakdown.get('pending', 0),
                    'processing': status_breakdown.get('processing', 0),
                    'failed': status_breakdown.get('failed', 0)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get user image stats: {str(e)}")
            return {
                'total_images': 0,
                'total_size_bytes': 0,
                'total_size_formatted': '0 B',
                'average_size_bytes': 0,
                'average_size_formatted': '0 B',
                'recent_uploads_today': 0,
                'status_breakdown': {},
                'processing_rate': {
                    'completed': 0,
                    'pending': 0,
                    'processing': 0,
                    'failed': 0
                }
            }
    
    def cleanup_orphaned_files(self, user_id: Optional[int] = None) -> Dict[str, int]:
        try:
            cleaned_files = 0
            cleaned_thumbnails = 0
            
            query = Image.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            images = query.all()
            
            for image in images:
                file_cleaned = False
                thumbnail_cleaned = False
                
                if image.file_path and not os.path.exists(image.file_path):
                    if image.vector_id:
                        self.vector_service.remove_image_vector(image.vector_id)
                    db.session.delete(image)
                    file_cleaned = True
                
                if image.thumbnail_path and not os.path.exists(image.thumbnail_path):
                    image.thumbnail_path = None
                    thumbnail_cleaned = True
                
                if file_cleaned:
                    cleaned_files += 1
                if thumbnail_cleaned:
                    cleaned_thumbnails += 1
            
            db.session.commit()
            
            return {
                'cleaned_files': cleaned_files,
                'cleaned_thumbnails': cleaned_thumbnails
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Cleanup failed: {str(e)}")
            return {'cleaned_files': 0, 'cleaned_thumbnails': 0}
    
    def reprocess_failed_images(self, user_id: Optional[int] = None, limit: int = 10) -> Dict[str, Any]:
        try:
            query = Image.query.filter_by(status='failed')
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            failed_images = query.limit(limit).all()
            
            results = {
                'reprocessed': [],
                'still_failed': [],
                'total_attempted': len(failed_images)
            }
            
            for image in failed_images:
                image.status = 'pending'
                image.processing_error = None
                db.session.commit()
                
                if self.process_single_image(image.id):
                    results['reprocessed'].append(image.id)
                else:
                    results['still_failed'].append(image.id)
            
            return results
        
        except Exception as e:
            logger.error(f"Reprocess failed images error: {str(e)}")
            return {
                'reprocessed': [],
                'still_failed': [],
                'total_attempted': 0,
                'error': str(e)
            }
    
    def get_processing_queue_status(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            query = Image.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            pending_count = query.filter_by(status='pending').count()
            processing_count = query.filter_by(status='processing').count()
            failed_count = query.filter_by(status='failed').count()
            completed_count = query.filter_by(status='completed').count()
            
            return {
                'queue_status': {
                    'pending': pending_count,
                    'processing': processing_count,
                    'failed': failed_count,
                    'completed': completed_count
                },
                'total_in_queue': pending_count + processing_count,
                'needs_attention': failed_count,
                'processing_healthy': failed_count < (pending_count + processing_count + completed_count) * 0.1
            }
        
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {
                'queue_status': {'pending': 0, 'processing': 0, 'failed': 0, 'completed': 0},
                'total_in_queue': 0,
                'needs_attention': 0,
                'processing_healthy': True
            }
    
    def search_by_metadata(self, user_id: int, filters: Dict[str, Any], 
                          limit: int = 20) -> List[Dict[str, Any]]:
        try:
            query = Image.query.filter_by(user_id=user_id, status='completed')
            
            if 'date_range' in filters:
                start_date = filters['date_range'].get('start')
                end_date = filters['date_range'].get('end')
                if start_date:
                    query = query.filter(Image.image_date >= start_date)
                if end_date:
                    query = query.filter(Image.image_date <= end_date)
            
            if 'location' in filters:
                location_query = f"%{filters['location']}%"
                query = query.filter(Image.location.ilike(location_query))
            
            if 'file_size_range' in filters:
                min_size = filters['file_size_range'].get('min', 0)
                max_size = filters['file_size_range'].get('max', float('inf'))
                query = query.filter(
                    Image.file_size >= min_size,
                    Image.file_size <= max_size
                )
            
            if 'dimensions' in filters:
                min_width = filters['dimensions'].get('min_width', 0)
                min_height = filters['dimensions'].get('min_height', 0)
                query = query.filter(
                    Image.width >= min_width,
                    Image.height >= min_height
                )
            
            images = query.limit(limit).all()
            
            return [
                {
                    'id': img.id,
                    'metadata': img.to_dict()
                }
                for img in images
            ]
        
        except Exception as e:
            logger.error(f"Metadata search failed: {str(e)}")
            return []
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        return format_file_size(size_bytes)
    
    def health_check(self) -> Dict[str, Any]:
        try:
            vector_health = self.vector_service.health_check()
            
            total_images = Image.query.count()
            processing_images = Image.query.filter_by(status='processing').count()
            failed_images = Image.query.filter_by(status='failed').count()
            
            upload_dir_writable = os.access(self.upload_base_path, os.W_OK)
            
            return {
                'healthy': vector_health.get('healthy', False) and upload_dir_writable,
                'vector_service': vector_health,
                'storage': {
                    'upload_directory_writable': upload_dir_writable,
                    'base_path': self.upload_base_path
                },
                'processing_stats': {
                    'total_images': total_images,
                    'currently_processing': processing_images,
                    'failed_processing': failed_images,
                    'processing_healthy': failed_images < total_images * 0.05  # Less than 5% failure rate
                }
            }
        
        except Exception as e:
            logger.error(f"Image service health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e)
            }