import logging
from typing import List, Dict, Any
from celery import shared_task
from datetime import datetime, timedelta

from extensions import db
from models.image import Image
from models.face import Face
from models.user import User
from services.face_service import FaceService
from services.email_service import EmailService
from middleware.audit_logger import AuditLogger
from utils.time_utils import now as harare_now
import os

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def process_faces_async(self, image_ids: List[int]):
    try:
        if not image_ids:
            logger.warning("No image IDs provided for face processing")
            return {'success': False, 'error': 'No image IDs provided'}
        
        logger.info(f"Starting face processing for {len(image_ids)} images")
        
        face_service = FaceService()
        
        results = {
            'total_images': len(image_ids),
            'processed_images': 0,
            'failed_images': 0,
            'total_faces_detected': 0,
            'total_faces_processed': 0,
            'total_faces_failed': 0,
            'image_results': [],
            'start_time': harare_now().isoformat()
        }
        
        for image_id in image_ids:
            try:
                image = Image.query.get(image_id)
                if not image:
                    logger.warning(f"Image {image_id} not found, skipping")
                    results['failed_images'] += 1
                    results['image_results'].append({
                        'image_id': image_id,
                        'success': False,
                        'error': 'Image not found'
                    })
                    continue
                
                if image.status != 'completed':
                    logger.warning(f"Image {image_id} not in completed status, skipping")
                    results['failed_images'] += 1
                    results['image_results'].append({
                        'image_id': image_id,
                        'success': False,
                        'error': 'Image not completed'
                    })
                    continue
                
                face_result = face_service.process_image_faces(image_id)
                
                if 'error' in face_result:
                    logger.error(f"Face processing failed for image {image_id}: {face_result['error']}")
                    results['failed_images'] += 1
                    results['image_results'].append({
                        'image_id': image_id,
                        'success': False,
                        'error': face_result['error']
                    })
                else:
                    results['processed_images'] += 1
                    results['total_faces_detected'] += face_result['faces_detected']
                    results['total_faces_processed'] += face_result['faces_processed']
                    results['total_faces_failed'] += face_result['faces_failed']
                    
                    results['image_results'].append({
                        'image_id': image_id,
                        'success': True,
                        'faces_detected': face_result['faces_detected'],
                        'faces_processed': face_result['faces_processed'],
                        'faces_failed': face_result['faces_failed']
                    })
                
                AuditLogger.log_face_detection(
                    user_id=image.user_id,
                    image_id=image_id,
                    face_count=face_result.get('faces_detected', 0),
                    ip_address='background_task',
                    success='error' not in face_result
                )
                
            except Exception as image_error:
                logger.error(f"Error processing faces for image {image_id}: {str(image_error)}")
                results['failed_images'] += 1
                results['image_results'].append({
                    'image_id': image_id,
                    'success': False,
                    'error': str(image_error)
                })
        
        results['end_time'] = harare_now().isoformat()
        
        logger.info(f"Face processing completed: {results['processed_images']} images processed, "
                   f"{results['total_faces_detected']} faces detected, "
                   f"{results['total_faces_processed']} faces processed successfully")
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Face processing task failed: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying face processing (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'retries_exhausted': True
        }

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def cluster_faces_async(self, user_id: int):
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for face clustering")
            return {'success': False, 'error': 'User not found'}
        
        logger.info(f"Starting face clustering for user {user_id}")
        
        face_service = FaceService()
        
        clustering_results = face_service.cluster_user_faces(user_id)
        
        if 'error' in clustering_results:
            logger.error(f"Face clustering failed for user {user_id}: {clustering_results['error']}")
            return {
                'success': False,
                'user_id': user_id,
                'error': clustering_results['error']
            }
        
        logger.info(f"Face clustering completed for user {user_id}: "
                   f"{clustering_results['clusters_created']} clusters created, "
                   f"{clustering_results['faces_clustered']} faces clustered")
        
        AuditLogger.log_resource_access(
            resource_type='face',
            resource_id=f"clustering_user_{user_id}",
            action='cluster',
            user_id=user_id,
            ip_address='background_task',
            status='success'
        )
        
        try:
            email_service = EmailService()
            if clustering_results['clusters_created'] > 0:
                email_service.send_template_email(
                    to_email=user.email,
                    subject="Face Clustering Complete - Image Search",
                    template_name="clustering_complete.html",
                    template_data={
                        'name': user.name,
                        'clusters_created': clustering_results['clusters_created'],
                        'faces_clustered': clustering_results['faces_clustered'],
                        'total_faces': clustering_results['total_faces']
                    }
                )
        except Exception as email_error:
            logger.warning(f"Failed to send clustering notification email: {str(email_error)}")
        
        return {
            'success': True,
            'user_id': user_id,
            'results': clustering_results
        }
    
    except Exception as e:
        logger.error(f"Face clustering task failed for user {user_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying face clustering for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=300 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e),
            'retries_exhausted': True
        }

@shared_task
def process_pending_faces():
    try:
        logger.info("Starting processing of pending faces")
        
        pending_images = Image.query.filter(
            Image.status == 'completed',
            ~Image.id.in_(
                db.session.query(Face.image_id).distinct()
            )
        ).limit(50).all()
        
        if not pending_images:
            logger.info("No pending face processing found")
            return {
                'success': True,
                'message': 'No pending face processing',
                'processed_count': 0
            }
        
        image_ids = [img.id for img in pending_images]
        
        process_faces_async.delay(image_ids)
        
        logger.info(f"Queued {len(image_ids)} images for face processing")
        
        return {
            'success': True,
            'queued_images': len(image_ids),
            'message': f'Queued {len(image_ids)} images for face processing'
        }
    
    except Exception as e:
        logger.error(f"Process pending faces task error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def auto_cluster_user_faces(user_id: int = None):
    try:
        logger.info(f"Starting auto-clustering for user {user_id or 'all users'}")
        
        if user_id:
            users_to_process = [User.query.get(user_id)]
            if not users_to_process[0]:
                return {'success': False, 'error': 'User not found'}
        else:
            users_to_process = User.query.filter_by(is_active=True).all()
        
        results = {
            'users_processed': 0,
            'total_clusters_created': 0,
            'total_faces_clustered': 0,
            'user_results': []
        }
        
        for user in users_to_process:
            try:
                unprocessed_faces_count = Face.query.join(Image).filter(
                    Image.user_id == user.id,
                    Face.status == 'processed',
                    Face.face_cluster_id.is_(None)
                ).count()
                
                if unprocessed_faces_count >= 2:
                    cluster_faces_async.delay(user.id)
                    
                    results['users_processed'] += 1
                    results['user_results'].append({
                        'user_id': user.id,
                        'unprocessed_faces': unprocessed_faces_count,
                        'clustering_queued': True
                    })
                else:
                    results['user_results'].append({
                        'user_id': user.id,
                        'unprocessed_faces': unprocessed_faces_count,
                        'clustering_queued': False,
                        'reason': 'Not enough faces for clustering'
                    })
                    
            except Exception as user_error:
                logger.warning(f"Failed to process clustering for user {user.id}: {str(user_error)}")
                results['user_results'].append({
                    'user_id': user.id,
                    'clustering_queued': False,
                    'error': str(user_error)
                })
        
        logger.info(f"Auto-clustering completed: {results['users_processed']} users queued for clustering")
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Auto-clustering task error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def cleanup_failed_face_processing():
    try:
        logger.info("Starting cleanup of failed face processing")
        
        cutoff_time = harare_now() - timedelta(hours=24)
        
        stuck_faces = Face.query.filter(
            Face.status == 'pending',
            Face.created_at < cutoff_time
        ).all()
        
        cleanup_count = 0
        for face in stuck_faces:
            try:
                if not os.path.exists(face.file_path):
                    db.session.delete(face)
                    cleanup_count += 1
                else:
                    face.mark_failed("Cleanup: Processing timeout")
                    cleanup_count += 1
            except Exception as face_error:
                logger.warning(f"Failed to cleanup face {face.id}: {str(face_error)}")
        
        db.session.commit()
        
        logger.info(f"Face cleanup completed: {cleanup_count} faces cleaned up")
        
        return {
            'success': True,
            'cleanup_count': cleanup_count
        }
    
    except Exception as e:
        logger.error(f"Face cleanup task error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def generate_face_processing_report(user_id: int):
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        face_service = FaceService()
        stats = face_service.get_user_face_stats(user_id)
        clusters = face_service.get_face_clusters_for_user(user_id)
        
        report_data = {
            'user_name': user.name,
            'user_email': user.email,
            'report_date': harare_now().isoformat(),
            'face_statistics': stats,
            'face_clusters': clusters[:10],  # Top 10 clusters
            'recommendations': []
        }
        
        if stats['processing_health']['failed'] > 0:
            report_data['recommendations'].append(
                f"You have {stats['processing_health']['failed']} failed face detections that may need attention."
            )
        
        if stats['unique_clusters'] > 0 and stats['unique_persons'] == 0:
            report_data['recommendations'].append(
                "Consider assigning names to your face clusters to better organize your photos."
            )
        
        if len(clusters) > 20:
            report_data['recommendations'].append(
                "You have many face clusters. Consider reviewing and merging similar ones."
            )
        
        return {
            'success': True,
            'report': report_data
        }
    
    except Exception as e:
        logger.error(f"Face processing report generation error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def update_face_embeddings():
    try:
        logger.info("Starting face embedding updates")
        
        faces_without_embeddings = Face.query.filter(
            Face.status == 'processed',
            Face.embedding_vector.is_(None)
        ).limit(100).all()
        
        if not faces_without_embeddings:
            logger.info("No faces need embedding updates")
            return {
                'success': True,
                'updated_count': 0,
                'message': 'No faces need embedding updates'
            }
        
        face_service = FaceService()
        updated_count = 0
        failed_count = 0
        
        for face in faces_without_embeddings:
            try:
                if os.path.exists(face.file_path):
                    embedding = face_service.generate_face_embedding(face.file_path)
                    if embedding is not None:
                        metadata = {
                            'image_id': face.image_id,
                            'face_id': face.face_id,
                            'confidence_score': face.confidence_score,
                            'quality_score': face.quality_score
                        }
                        
                        if face_service.vector_service.store_face_vector(face.face_id, embedding, metadata):
                            updated_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                else:
                    face.mark_failed("Face file not found")
                    failed_count += 1
                    
            except Exception as face_error:
                logger.warning(f"Failed to update embedding for face {face.id}: {str(face_error)}")
                failed_count += 1
        
        db.session.commit()
        
        logger.info(f"Face embedding update completed: {updated_count} updated, {failed_count} failed")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'failed_count': failed_count
        }
    
    except Exception as e:
        logger.error(f"Face embedding update task error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
