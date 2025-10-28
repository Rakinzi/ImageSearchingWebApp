from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index
from extensions import db
from utils.time_utils import now as harare_now

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    reset_password_token = db.Column(db.String(100), nullable=True)
    reset_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)
    
    created_at = db.Column(db.DateTime(timezone=True), default=harare_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=harare_now, onupdate=harare_now, nullable=False)
    
    images = db.relationship('Image', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    __table_args__ = (
        Index('ix_users_email_active', 'email', 'is_active'),
        Index('ix_users_verification_token', 'verification_token'),
        Index('ix_users_reset_token', 'reset_password_token'),
        Index('ix_users_created_at', 'created_at'),
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_login_info(self, ip_address=None):
        self.last_login_at = harare_now()
        self.last_login_ip = ip_address
        self.login_count += 1
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'is_admin': self.is_admin,
                'last_login_ip': self.last_login_ip
            })
        
        return data
    
    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email.lower()).first()
    
    @classmethod
    def get_active_users(cls):
        return cls.query.filter_by(is_active=True).all()
    
    def __repr__(self):
        return f'<User {self.email}>'
