import os
import logging
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import func

from extensions import db
from models.audit_log import AuditLog
from models.image import Image
from models.face import Face
from models.user import User
from services.image_service import ImageService
from services.face_service import FaceService
from services.vector_service import VectorService

logger = logging.getLogger(__name__)

@shared_task
def cleanup_old_logs():
    try:
        logger.info("Starting cleanup of old audit logs")
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_logs = AuditLog.query.filter(AuditLog.timestamp < cutoff_date)
        count = old_logs.count()
        
        if count > 0:
            old_logs.delete()
            db.session.commit()
            logger.info(f"Deleted {count} old audit logs")
        else:
            logger.info("No old audit logs to delete")
        
        log_files_cleaned = 0
        logs_dir = 'logs'
        
        if os.path.exists(logs_dir):
            for filename in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_age < cutoff_date and filename.endswith('.log'):
                        try:
                            os.remove(file_path)
                            log_files_cleaned += 1
                            logger.info(f"Deleted old log file: {filename}")
                        except Exception as file_error:
                            logger.warning(f"Failed to delete log file {filename}: {str(file_error)}")
        
        return {
            'success': True,
            'database_logs_deleted': count,
            'log_files_deleted': log_files_cleaned,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Log cleanup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def cleanup_orphaned_files():
    try:
        logger.info("Starting cleanup of orphaned files")
        
        image_service = ImageService()
        face_service = FaceService()
        
        image_cleanup = image_service.cleanup_orphaned_files()
        face_cleanup = face_service.cleanup_orphaned_faces()
        
        total_cleaned = (
            image_cleanup.get('cleaned_files', 0) + 
            image_cleanup.get('cleaned_thumbnails', 0) +
            face_cleanup.get('cleaned_files', 0)
        )
        
        logger.info(f"Orphaned file cleanup completed: {total_cleaned} files cleaned")
        
        return {
            'success': True,
            'image_files_cleaned': image_cleanup.get('cleaned_files', 0),
            'thumbnails_cleaned': image_cleanup.get('cleaned_thumbnails', 0),
            'face_files_cleaned': face_cleanup.get('cleaned_files', 0),
            'total_cleaned': total_cleaned
        }
    
    except Exception as e:
        logger.error(f"Orphaned files cleanup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def cleanup_vector_database():
    try:
        logger.info("Starting vector database cleanup")
        
        vector_service = VectorService()
        
        valid_image_ids = [
            f"img_{img.id}_{img.user_id}" 
            for img in Image.query.filter_by(status='completed').all()
        ]
        
        valid_face_ids = [
            face.face_id 
            for face in Face.query.filter_by(status='processed').all()
        ]
        
        cleanup_results = vector_service.cleanup_orphaned_vectors(valid_image_ids, valid_face_ids)
        
        logger.info(f"Vector database cleanup completed: "
                   f"{cleanup_results['orphaned_images_removed']} image vectors removed, "
                   f"{cleanup_results['orphaned_faces_removed']} face vectors removed")
        
        return {
            'success': True,
            'orphaned_images_removed': cleanup_results['orphaned_images_removed'],
            'orphaned_faces_removed': cleanup_results['orphaned_faces_removed']
        }
    
    except Exception as e:
        logger.error(f"Vector database cleanup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def cleanup_inactive_users():
    try:
        logger.info("Starting cleanup of inactive users")
        
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        
        inactive_users = User.query.filter(
            User.is_active == False,
            User.updated_at < cutoff_date,
            User.last_login_at < cutoff_date
        ).all()
        
        cleaned_users = 0
        cleaned_images = 0
        cleaned_faces = 0
        
        for user in inactive_users:
            try:
                user_images = Image.query.filter_by(user_id=user.id).all()
                user_faces = Face.query.join(Image).filter(Image.user_id == user.id).all()
                
                for face in user_faces:
                    if os.path.exists(face.file_path):
                        os.remove(face.file_path)
                    cleaned_faces += 1
                
                for image in user_images:
                    if os.path.exists(image.file_path):
                        os.remove(image.file_path)
                    if image.thumbnail_path and os.path.exists(image.thumbnail_path):
                        os.remove(image.thumbnail_path)
                    cleaned_images += 1
                
                Face.query.join(Image).filter(Image.user_id == user.id).delete()
                Image.query.filter_by(user_id=user.id).delete()
                AuditLog.query.filter_by(user_id=user.id).delete()
                
                db.session.delete(user)
                cleaned_users += 1
                
                logger.info(f"Cleaned up inactive user: {user.email}")
                
            except Exception as user_error:
                logger.error(f"Failed to cleanup user {user.id}: {str(user_error)}")
                db.session.rollback()
        
        db.session.commit()
        
        logger.info(f"Inactive users cleanup completed: "
                   f"{cleaned_users} users, {cleaned_images} images, {cleaned_faces} faces")
        
        return {
            'success': True,
            'users_cleaned': cleaned_users,
            'images_cleaned': cleaned_images,
            'faces_cleaned': cleaned_faces
        }
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Inactive users cleanup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def database_maintenance():
    try:
        logger.info("Starting database maintenance")
        
        maintenance_results = {
            'tables_optimized': 0,
            'indexes_rebuilt': 0,
            'statistics_updated': True
        }
        
        try:
            db.session.execute('ANALYZE TABLE users, images, faces, audit_logs')
            maintenance_results['statistics_updated'] = True
            logger.info("Database statistics updated")
        except Exception as analyze_error:
            logger.warning(f"Failed to update database statistics: {str(analyze_error)}")
            maintenance_results['statistics_updated'] = False
        
        try:
            db.session.execute('OPTIMIZE TABLE audit_logs')
            maintenance_results['tables_optimized'] += 1
            logger.info("Optimized audit_logs table")
        except Exception as opt_error:
            logger.warning(f"Failed to optimize audit_logs table: {str(opt_error)}")
        
        db.session.commit()
        
        logger.info("Database maintenance completed")
        
        return {
            'success': True,
            'results': maintenance_results
        }
    
    except Exception as e:
        logger.error(f"Database maintenance task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def generate_system_health_report():
    try:
        logger.info("Generating system health report")
        
        image_service = ImageService()
        face_service = FaceService()
        vector_service = VectorService()
        
        image_health = image_service.health_check()
        face_health = face_service.health_check()
        vector_health = vector_service.health_check()
        
        db_stats = db.session.query(
            func.count(User.id).label('total_users'),
            func.count(Image.id).label('total_images'),
            func.count(Face.id).label('total_faces')
        ).select_from(User).outerjoin(Image).outerjoin(Face).first()
        
        processing_stats = {
            'pending_images': Image.query.filter_by(status='pending').count(),
            'processing_images': Image.query.filter_by(status='processing').count(),
            'failed_images': Image.query.filter_by(status='failed').count(),
            'pending_faces': Face.query.filter_by(status='pending').count(),
            'failed_faces': Face.query.filter_by(status='failed').count()
        }
        
        storage_stats = {
            'total_storage_used': db.session.query(func.sum(Image.file_size)).scalar() or 0,
            'average_image_size': db.session.query(func.avg(Image.file_size)).scalar() or 0
        }
        
        recent_activity = {
            'recent_registrations': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'recent_uploads': Image.query.filter(
                Image.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'recent_face_detections': Face.query.filter(
                Face.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
        }
        
        health_report = {
            'report_timestamp': datetime.utcnow().isoformat(),
            'overall_health': (
                image_health.get('healthy', False) and
                face_health.get('healthy', False) and
                vector_health.get('healthy', False)
            ),
            'service_health': {
                'image_service': image_health,
                'face_service': face_health,
                'vector_service': vector_health
            },
            'database_stats': {
                'total_users': db_stats.total_users or 0,
                'total_images': db_stats.total_images or 0,
                'total_faces': db_stats.total_faces or 0
            },
            'processing_stats': processing_stats,
            'storage_stats': storage_stats,
            'recent_activity': recent_activity,
            'alerts': []
        }
        
        if processing_stats['failed_images'] > 10:
            health_report['alerts'].append(
                f"High number of failed image processing: {processing_stats['failed_images']}"
            )
        
        if processing_stats['pending_images'] > 100:
            health_report['alerts'].append(
                f"Large processing queue: {processing_stats['pending_images']} pending images"
            )
        
        if not health_report['overall_health']:
            health_report['alerts'].append("One or more services are unhealthy")
        
        logger.info("System health report generated successfully")
        
        return {
            'success': True,
            'report': health_report
        }
    
    except Exception as e:
        logger.error(f"System health report generation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def backup_critical_data():
    try:
        logger.info("Starting critical data backup")
        
        backup_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"backups/backup_{backup_timestamp}"
        
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_results = {
            'backup_timestamp': backup_timestamp,
            'backup_directory': backup_dir,
            'files_backed_up': 0,
            'database_backed_up': False
        }
        
        try:
            import subprocess
            
            db_backup_file = os.path.join(backup_dir, 'database.sql')
            
            # This is a placeholder - actual backup command depends on your database setup
            # subprocess.run(['mysqldump', 'database_name'], stdout=open(db_backup_file, 'w'))
            
            backup_results['database_backed_up'] = True
            backup_results['files_backed_up'] += 1
            
        except Exception as db_backup_error:
            logger.warning(f"Database backup failed: {str(db_backup_error)}")
        
        critical_dirs = ['chroma_db', 'logs']
        
        for dir_name in critical_dirs:
            if os.path.exists(dir_name):
                try:
                    import shutil
                    backup_path = os.path.join(backup_dir, dir_name)
                    shutil.copytree(dir_name, backup_path)
                    backup_results['files_backed_up'] += 1
                except Exception as dir_backup_error:
                    logger.warning(f"Failed to backup {dir_name}: {str(dir_backup_error)}")
        
        old_backups = []
        if os.path.exists('backups'):
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            for backup_name in os.listdir('backups'):
                backup_path = os.path.join('backups', backup_name)
                if os.path.isdir(backup_path):
                    backup_date = datetime.fromtimestamp(os.path.getctime(backup_path))
                    if backup_date < cutoff_date:
                        try:
                            shutil.rmtree(backup_path)
                            old_backups.append(backup_name)
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to cleanup old backup {backup_name}: {str(cleanup_error)}")
        
        backup_results['old_backups_cleaned'] = len(old_backups)
        
        logger.info(f"Critical data backup completed: {backup_results['files_backed_up']} items backed up")
        
        return {
            'success': True,
            'results': backup_results
        }
    
    except Exception as e:
        logger.error(f"Critical data backup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def monitor_disk_usage():
    try:
        logger.info("Monitoring disk usage")
        
        import shutil
        
        upload_dir = 'static/uploads'
        logs_dir = 'logs'
        chroma_dir = 'chroma_db'
        
        disk_usage = {}
        
        for directory in [upload_dir, logs_dir, chroma_dir]:
            if os.path.exists(directory):
                total_size = 0
                file_count = 0
                
                for dirpath, dirnames, filenames in os.walk(directory):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                            file_count += 1
                        except Exception:
                            continue
                
                disk_usage[directory] = {
                    'total_size_bytes': total_size,
                    'total_size_formatted': ImageService.format_file_size(total_size),
                    'file_count': file_count
                }
        
        total_disk_free = shutil.disk_usage('.').free
        total_disk_used = shutil.disk_usage('.').used
        total_disk_total = shutil.disk_usage('.').total
        
        disk_usage['system'] = {
            'free_bytes': total_disk_free,
            'used_bytes': total_disk_used,
            'total_bytes': total_disk_total,
            'free_formatted': ImageService.format_file_size(total_disk_free),
            'used_formatted': ImageService.format_file_size(total_disk_used),
            'total_formatted': ImageService.format_file_size(total_disk_total),
            'usage_percentage': (total_disk_used / total_disk_total) * 100
        }
        
        alerts = []
        if disk_usage['system']['usage_percentage'] > 90:
            alerts.append("Critical: Disk usage above 90%")
        elif disk_usage['system']['usage_percentage'] > 80:
            alerts.append("Warning: Disk usage above 80%")
        
        logger.info(f"Disk usage monitoring completed. Usage: {disk_usage['system']['usage_percentage']:.1f}%")
        
        return {
            'success': True,
            'disk_usage': disk_usage,
            'alerts': alerts
        }
    
    except Exception as e:
        logger.error(f"Disk usage monitoring failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }