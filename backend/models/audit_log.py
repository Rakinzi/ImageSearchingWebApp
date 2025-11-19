from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from extensions import db
from datetime import timedelta
from utils.time_utils import now as harare_now

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    event_type = db.Column(db.String(100), nullable=False, index=True)
    event_category = db.Column(db.String(50), nullable=False, index=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True, index=True)
    
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    resource_type = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.String(100), nullable=True)
    
    action = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.Enum('success', 'failure', 'error', name='audit_status'), 
                      nullable=False, index=True)
    
    request_method = db.Column(db.String(10), nullable=True)
    request_path = db.Column(db.String(500), nullable=True)
    request_data = db.Column(JSONB, nullable=True)

    response_status_code = db.Column(db.Integer, nullable=True)
    response_data = db.Column(JSONB, nullable=True)

    error_message = db.Column(Text, nullable=True)
    additional_data = db.Column(JSONB, nullable=True)
    
    risk_level = db.Column(db.Enum('low', 'medium', 'high', 'critical', name='risk_level'), 
                          default='low', nullable=False, index=True)
    
    timestamp = db.Column(db.DateTime(timezone=True), default=harare_now, nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_logs_event_timestamp', 'event_type', 'timestamp'),
        Index('ix_audit_logs_status_timestamp', 'status', 'timestamp'),
        Index('ix_audit_logs_risk_timestamp', 'risk_level', 'timestamp'),
        Index('ix_audit_logs_ip_timestamp', 'ip_address', 'timestamp'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id', 'timestamp'),
        Index('ix_audit_logs_category_timestamp', 'event_category', 'timestamp'),
    )
    
    @classmethod
    def log_auth_event(cls, event_type, user_id=None, ip_address=None, user_agent=None, 
                      status='success', error_message=None, session_id=None):
        log_entry = cls(
            event_type=event_type,
            event_category='authentication',
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action=event_type,
            status=status,
            error_message=error_message,
            risk_level='medium' if status == 'failure' else 'low'
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def log_api_request(cls, request, response=None, user_id=None, error_message=None):
        status = 'success'
        risk_level = 'low'
        
        if response and response.status_code >= 400:
            status = 'failure' if response.status_code < 500 else 'error'
            risk_level = 'medium' if response.status_code < 500 else 'high'
        
        log_entry = cls(
            event_type='api_request',
            event_category='api',
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            action=request.method,
            status=status,
            request_method=request.method,
            request_path=request.path,
            response_status_code=response.status_code if response else None,
            error_message=error_message,
            risk_level=risk_level
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def log_resource_access(cls, resource_type, resource_id, action, user_id=None, 
                           ip_address=None, status='success', error_message=None):
        risk_level = 'low'
        if action in ['delete', 'modify'] and resource_type in ['image', 'face']:
            risk_level = 'medium'
        
        log_entry = cls(
            event_type='resource_access',
            event_category='data',
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=str(resource_id),
            action=action,
            status=status,
            error_message=error_message,
            risk_level=risk_level
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def log_security_event(cls, event_type, user_id=None, ip_address=None, user_agent=None,
                          additional_data=None, risk_level='high'):
        log_entry = cls(
            event_type=event_type,
            event_category='security',
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action=event_type,
            status='failure',
            additional_data=additional_data,
            risk_level=risk_level
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def get_security_summary(cls, hours=24):
        from sqlalchemy import func
        cutoff = harare_now() - timedelta(hours=hours)
        
        return db.session.query(
            cls.event_category,
            cls.risk_level,
            func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= cutoff
        ).group_by(
            cls.event_category,
            cls.risk_level
        ).all()
    
    @classmethod
    def get_failed_logins(cls, hours=24, limit=100):
        cutoff = harare_now() - timedelta(hours=hours)
        
        return cls.query.filter(
            cls.event_category == 'authentication',
            cls.status == 'failure',
            cls.timestamp >= cutoff
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'status': self.status,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'response_status_code': self.response_status_code,
            'error_message': self.error_message,
            'risk_level': self.risk_level,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f'<AuditLog {self.event_type} - {self.status} - {self.timestamp}>'
