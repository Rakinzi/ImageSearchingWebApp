from flask import Blueprint, request, jsonify, current_app
from flask_smorest import Blueprint as SmorestBlueprint
from marshmallow import Schema, fields, validate
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from extensions import db, limiter
from models.user import User
from models.audit_log import AuditLog
from models.image import Image
from models.face import Face
from middleware.auth import require_admin
from middleware.audit_logger import AuditLogger
from utils.validators import validate_pagination
from utils.security import sanitize_input

admin_bp = SmorestBlueprint('admin', __name__, description='Administrative operations')

class AuditLogListSchema(Schema):
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=50, validate=validate.Range(min=1, max=200))
    event_type = fields.Str(missing=None)
    event_category = fields.Str(missing=None, validate=validate.OneOf(['authentication', 'api', 'data', 'security']))
    status = fields.Str(missing=None, validate=validate.OneOf(['success', 'failure', 'error']))
    risk_level = fields.Str(missing=None, validate=validate.OneOf(['low', 'medium', 'high', 'critical']))
    user_id = fields.Int(missing=None)
    start_date = fields.DateTime(missing=None)
    end_date = fields.DateTime(missing=None)
    ip_address = fields.Str(missing=None)

class UserManagementSchema(Schema):
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=20, validate=validate.Range(min=1, max=100))
    is_active = fields.Bool(missing=None)
    is_verified = fields.Bool(missing=None)
    is_admin = fields.Bool(missing=None)
    search = fields.Str(missing=None, validate=validate.Length(max=100))

class UserUpdateSchema(Schema):
    is_active = fields.Bool(missing=None)
    is_verified = fields.Bool(missing=None)
    is_admin = fields.Bool(missing=None)

class SystemStatsSchema(Schema):
    include_user_breakdown = fields.Bool(missing=False)
    include_processing_stats = fields.Bool(missing=False)
    time_range_hours = fields.Int(missing=24, validate=validate.Range(min=1, max=8760))

@admin_bp.route('/audit-logs', methods=['GET'])
@admin_bp.arguments(AuditLogListSchema, location='query')
@require_admin
@limiter.limit("100 per hour")
def get_audit_logs(query_args, current_user):
    try:
        page = query_args.get('page', 1)
        per_page = query_args.get('per_page', 50)
        event_type = query_args.get('event_type')
        event_category = query_args.get('event_category')
        status = query_args.get('status')
        risk_level = query_args.get('risk_level')
        user_id = query_args.get('user_id')
        start_date = query_args.get('start_date')
        end_date = query_args.get('end_date')
        ip_address = query_args.get('ip_address')
        
        query = AuditLog.query
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if event_category:
            query = query.filter(AuditLog.event_category == event_category)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        if risk_level:
            query = query.filter(AuditLog.risk_level == risk_level)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        query = query.order_by(desc(AuditLog.timestamp))
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        audit_logs = []
        for log in pagination.items:
            log_dict = log.to_dict()
            if log.user_id:
                user = User.query.get(log.user_id)
                log_dict['user_email'] = user.email if user else None
            audit_logs.append(log_dict)
        
        AuditLogger.log_resource_access(
            resource_type='audit_log',
            resource_id='batch_query',
            action='view',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify({
            'audit_logs': audit_logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get audit logs error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve audit logs'}), 500

@admin_bp.route('/audit-logs/summary', methods=['GET'])
@require_admin
@limiter.limit("50 per hour")
def get_audit_summary(current_user):
    try:
        hours = request.args.get('hours', 24, type=int)
        if hours > 8760:  # Max 1 year
            hours = 8760
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        summary_data = db.session.query(
            AuditLog.event_category,
            AuditLog.risk_level,
            AuditLog.status,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= cutoff
        ).group_by(
            AuditLog.event_category,
            AuditLog.risk_level,
            AuditLog.status
        ).all()
        
        failed_logins = AuditLog.get_failed_logins(hours=hours, limit=20)
        
        high_risk_events = AuditLog.query.filter(
            AuditLog.timestamp >= cutoff,
            AuditLog.risk_level.in_(['high', 'critical'])
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        top_ips = db.session.query(
            AuditLog.ip_address,
            func.count(AuditLog.id).label('request_count')
        ).filter(
            AuditLog.timestamp >= cutoff,
            AuditLog.ip_address.isnot(None)
        ).group_by(AuditLog.ip_address).order_by(
            desc('request_count')
        ).limit(10).all()
        
        summary = {
            'time_range_hours': hours,
            'category_breakdown': {},
            'risk_breakdown': {},
            'status_breakdown': {},
            'failed_login_attempts': len(failed_logins),
            'recent_failed_logins': [log.to_dict() for log in failed_logins[:5]],
            'high_risk_events': [event.to_dict() for event in high_risk_events],
            'top_ip_addresses': [{'ip': ip, 'requests': count} for ip, count in top_ips]
        }
        
        for category, risk, status, count in summary_data:
            if category not in summary['category_breakdown']:
                summary['category_breakdown'][category] = 0
            summary['category_breakdown'][category] += count
            
            if risk not in summary['risk_breakdown']:
                summary['risk_breakdown'][risk] = 0
            summary['risk_breakdown'][risk] += count
            
            if status not in summary['status_breakdown']:
                summary['status_breakdown'][status] = 0
            summary['status_breakdown'][status] += count
        
        return jsonify(summary), 200
        
    except Exception as e:
        current_app.logger.error(f"Get audit summary error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve audit summary'}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_bp.arguments(UserManagementSchema, location='query')
@require_admin
@limiter.limit("100 per hour")
def list_users(query_args, current_user):
    try:
        page = query_args.get('page', 1)
        per_page = query_args.get('per_page', 20)
        is_active = query_args.get('is_active')
        is_verified = query_args.get('is_verified')
        is_admin = query_args.get('is_admin')
        search = query_args.get('search')
        
        query = User.query
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        if search:
            search_term = f"%{sanitize_input(search)}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search_term),
                    User.name.ilike(search_term)
                )
            )
        
        query = query.order_by(desc(User.created_at))
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            user_dict = user.to_dict(include_sensitive=True)
            
            image_count = Image.query.filter_by(user_id=user.id).count()
            face_count = Face.query.join(Image).filter(Image.user_id == user.id).count()
            
            user_dict.update({
                'image_count': image_count,
                'face_count': face_count
            })
            users.append(user_dict)
        
        AuditLogger.log_resource_access(
            resource_type='user',
            resource_id='batch_query',
            action='list',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"List users error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
@limiter.limit("200 per hour")
def get_user_details(user_id, current_user):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_dict = user.to_dict(include_sensitive=True)
        
        recent_audit_logs = AuditLog.query.filter_by(
            user_id=user_id
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        image_stats = db.session.query(
            Image.status,
            func.count(Image.id).label('count')
        ).filter_by(user_id=user_id).group_by(Image.status).all()
        
        face_stats = db.session.query(
            Face.status,
            func.count(Face.id).label('count')
        ).join(Image).filter(Image.user_id == user_id).group_by(Face.status).all()
        
        user_dict.update({
            'recent_activity': [log.to_dict() for log in recent_audit_logs],
            'image_stats': {status: count for status, count in image_stats},
            'face_stats': {status: count for status, count in face_stats}
        })
        
        AuditLogger.log_resource_access(
            resource_type='user',
            resource_id=user_id,
            action='view_details',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify(user_dict), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user details error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user details'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@admin_bp.arguments(UserUpdateSchema)
@require_admin
@limiter.limit("50 per hour")
def update_user(json_data, user_id, current_user):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.id == current_user.id and 'is_admin' in json_data:
            return jsonify({'error': 'Cannot modify your own admin status'}), 400
        
        changes = []
        
        if 'is_active' in json_data and json_data['is_active'] != user.is_active:
            user.is_active = json_data['is_active']
            changes.append(f"is_active: {user.is_active}")
        
        if 'is_verified' in json_data and json_data['is_verified'] != user.is_verified:
            user.is_verified = json_data['is_verified']
            changes.append(f"is_verified: {user.is_verified}")
        
        if 'is_admin' in json_data and json_data['is_admin'] != user.is_admin:
            user.is_admin = json_data['is_admin']
            changes.append(f"is_admin: {user.is_admin}")
        
        if not changes:
            return jsonify({'message': 'No changes made'}), 200
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        AuditLogger.log_resource_access(
            resource_type='user',
            resource_id=user_id,
            action='update',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        additional_data = {
            'target_user_email': user.email,
            'changes_made': changes
        }
        
        AuditLog.log_security_event(
            event_type='user_account_modified',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            additional_data=additional_data,
            risk_level='medium'
        )
        
        return jsonify({
            'message': 'User updated successfully',
            'changes': changes,
            'user': user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/system/stats', methods=['GET'])
@admin_bp.arguments(SystemStatsSchema, location='query')
@require_admin
@limiter.limit("50 per hour")
def get_system_stats(query_args, current_user):
    try:
        include_user_breakdown = query_args.get('include_user_breakdown', False)
        include_processing_stats = query_args.get('include_processing_stats', False)
        time_range_hours = query_args.get('time_range_hours', 24)
        
        cutoff = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        total_images = Image.query.count()
        total_faces = Face.query.count()
        
        recent_registrations = User.query.filter(
            User.created_at >= cutoff
        ).count()
        
        recent_uploads = Image.query.filter(
            Image.created_at >= cutoff
        ).count()
        
        storage_usage = db.session.query(
            func.sum(Image.file_size)
        ).scalar() or 0
        
        stats = {
            'system_overview': {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'admin_users': admin_users,
                'total_images': total_images,
                'total_faces': total_faces,
                'storage_usage_bytes': storage_usage,
                'storage_usage_formatted': format_file_size(storage_usage)
            },
            'recent_activity': {
                'time_range_hours': time_range_hours,
                'new_registrations': recent_registrations,
                'new_uploads': recent_uploads
            }
        }
        
        if include_user_breakdown:
            user_breakdown = db.session.query(
                func.count(Image.id).label('image_count'),
                func.sum(Image.file_size).label('storage_used'),
                User.email
            ).join(User).group_by(User.id, User.email).order_by(
                desc('image_count')
            ).limit(10).all()
            
            stats['top_users'] = [
                {
                    'email': email,
                    'image_count': count,
                    'storage_used': storage or 0,
                    'storage_formatted': format_file_size(storage or 0)
                }
                for count, storage, email in user_breakdown
            ]
        
        if include_processing_stats:
            processing_stats = db.session.query(
                Image.status,
                func.count(Image.id).label('count')
            ).group_by(Image.status).all()
            
            face_processing_stats = db.session.query(
                Face.status,
                func.count(Face.id).label('count')
            ).group_by(Face.status).all()
            
            stats['processing_breakdown'] = {
                'images': {status: count for status, count in processing_stats},
                'faces': {status: count for status, count in face_processing_stats}
            }
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f"Get system stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system statistics'}), 500

@admin_bp.route('/system/health', methods=['GET'])
@require_admin
@limiter.limit("100 per hour")
def get_system_health(current_user):
    try:
        health_status = {
            'database': 'unknown',
            'redis': 'unknown',
            'storage': 'unknown',
            'processing_queue': 'unknown'
        }
        
        try:
            db.session.execute('SELECT 1')
            health_status['database'] = 'healthy'
        except Exception:
            health_status['database'] = 'unhealthy'
        
        try:
            from extensions import cache
            if hasattr(cache, 'ping'):
                cache.ping()
            health_status['redis'] = 'healthy'
        except Exception:
            health_status['redis'] = 'unhealthy'
        
        try:
            import os
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
                health_status['storage'] = 'healthy'
            else:
                health_status['storage'] = 'unhealthy'
        except Exception:
            health_status['storage'] = 'unhealthy'
        
        try:
            from celery import current_app as celery_app
            inspect = celery_app.control.inspect()
            if inspect.active():
                health_status['processing_queue'] = 'healthy'
            else:
                health_status['processing_queue'] = 'unhealthy'
        except Exception:
            health_status['processing_queue'] = 'unknown'
        
        overall_health = 'healthy' if all(
            status == 'healthy' for status in health_status.values()
        ) else 'degraded'
        
        return jsonify({
            'overall_status': overall_health,
            'components': health_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"System health check error: {str(e)}")
        return jsonify({'error': 'Failed to check system health'}), 500

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"