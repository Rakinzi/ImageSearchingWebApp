import os
import json
import logging
from datetime import datetime
from flask import request, g
from flask_jwt_extended import get_jwt_identity
from models.audit_log import AuditLog
from extensions import db

def setup_audit_logging(app):
    os.makedirs('logs', exist_ok=True)
    
    audit_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    audit_handler = logging.FileHandler('logs/audit.log')
    audit_handler.setFormatter(audit_formatter)
    audit_handler.setLevel(logging.INFO)
    
    audit_logger = logging.getLogger('audit')
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        g.user_id = None
        
        try:
            g.user_id = get_jwt_identity()
        except Exception:
            pass
        
        excluded_paths = ['/health', '/metrics', '/static']
        if not any(request.path.startswith(path) for path in excluded_paths):
            audit_logger.info(
                f"REQUEST - Method: {request.method}, "
                f"Path: {request.path}, "
                f"IP: {request.remote_addr}, "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}, "
                f"User-ID: {g.user_id}"
            )
    
    @app.after_request
    def after_request(response):
        try:
            excluded_paths = ['/health', '/metrics', '/static']
            if not any(request.path.startswith(path) for path in excluded_paths):
                duration = None
                if hasattr(g, 'start_time'):
                    duration = (datetime.utcnow() - g.start_time).total_seconds()
                
                audit_logger.info(
                    f"RESPONSE - Status: {response.status_code}, "
                    f"Duration: {duration}s, "
                    f"Size: {response.content_length or 0} bytes"
                )
                
                if should_log_to_database(request, response):
                    try:
                        AuditLog.log_api_request(
                            request=request,
                            response=response,
                            user_id=getattr(g, 'user_id', None)
                        )
                    except Exception as e:
                        app.logger.error(f"Failed to log to database: {str(e)}")
        
        except Exception as e:
            app.logger.error(f"Audit logging error: {str(e)}")
        
        return response

def should_log_to_database(request, response):
    high_priority_paths = ['/auth', '/api/v1/images', '/api/v1/faces', '/api/v1/admin']
    sensitive_methods = ['POST', 'PUT', 'DELETE']
    error_statuses = range(400, 600)
    
    return (
        any(request.path.startswith(path) for path in high_priority_paths) or
        request.method in sensitive_methods or
        response.status_code in error_statuses
    )

class AuditLogger:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        setup_audit_logging(app)
    
    @staticmethod
    def log_login_attempt(user_id, ip_address, user_agent, success=True, error_message=None):
        status = 'success' if success else 'failure'
        event_type = 'login_success' if success else 'login_failed'
        
        AuditLog.log_auth_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
    
    @staticmethod
    def log_logout(user_id, ip_address, session_id):
        AuditLog.log_auth_event(
            event_type='logout',
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            status='success'
        )
    
    @staticmethod
    def log_password_change(user_id, ip_address, success=True):
        status = 'success' if success else 'failure'
        AuditLog.log_auth_event(
            event_type='password_change',
            user_id=user_id,
            ip_address=ip_address,
            status=status
        )
    
    @staticmethod
    def log_image_upload(user_id, image_id, filename, ip_address, success=True, error_message=None):
        status = 'success' if success else 'failure'
        AuditLog.log_resource_access(
            resource_type='image',
            resource_id=image_id,
            action='upload',
            user_id=user_id,
            ip_address=ip_address,
            status=status,
            error_message=error_message
        )
    
    @staticmethod
    def log_image_search(user_id, query, result_count, ip_address):
        additional_data = {
            'query': query,
            'result_count': result_count
        }
        
        log_entry = AuditLog(
            event_type='image_search',
            event_category='search',
            user_id=user_id,
            ip_address=ip_address,
            action='search',
            status='success',
            additional_data=additional_data,
            risk_level='low'
        )
        db.session.add(log_entry)
        db.session.commit()
    
    @staticmethod
    def log_face_detection(user_id, image_id, face_count, ip_address, success=True):
        status = 'success' if success else 'failure'
        additional_data = {
            'face_count': face_count,
            'image_id': image_id
        }
        
        log_entry = AuditLog(
            event_type='face_detection',
            event_category='processing',
            user_id=user_id,
            ip_address=ip_address,
            action='detect_faces',
            status=status,
            additional_data=additional_data,
            risk_level='low'
        )
        db.session.add(log_entry)
        db.session.commit()
    
    @staticmethod
    def log_suspicious_activity(event_type, ip_address, user_agent=None, user_id=None, 
                              additional_data=None, risk_level='high'):
        AuditLog.log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data,
            risk_level=risk_level
        )
    
    @staticmethod
    def log_rate_limit_exceeded(ip_address, endpoint, user_id=None):
        additional_data = {
            'endpoint': endpoint,
            'limit_type': 'rate_limit'
        }
        
        AuditLog.log_security_event(
            event_type='rate_limit_exceeded',
            user_id=user_id,
            ip_address=ip_address,
            additional_data=additional_data,
            risk_level='medium'
        )