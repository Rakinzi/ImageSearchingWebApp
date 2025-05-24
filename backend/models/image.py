from datetime import datetime
from sqlalchemy import Index, Text
from sqlalchemy.dialects.mysql import JSON
from extensions import db

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False, index=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)
    
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    
    checksum = db.Column(db.String(64), nullable=False, index=True)
    
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='image_status'), 
                      default='pending', nullable=False, index=True)
    
    extracted_text = db.Column(Text, nullable=True)
    image_date = db.Column(db.DateTime, nullable=True, index=True)
    location = db.Column(db.String(500), nullable=True)
    
    exif_data = db.Column(JSON, nullable=True)
    metadata = db.Column(JSON, nullable=True)
    
    vector_id = db.Column(db.String(255), nullable=True, index=True)
    embedding_version = db.Column(db.String(50), default='v1', nullable=False)
    
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    processing_error = db.Column(Text, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    faces = db.relationship('Face', backref='image', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('ix_images_user_status', 'user_id', 'status'),
        Index('ix_images_user_created', 'user_id', 'created_at'),
        Index('ix_images_checksum_user', 'checksum', 'user_id'),
        Index('ix_images_image_date', 'image_date'),
        Index('ix_images_location', 'location'),
        Index('ix_images_processing', 'status', 'processing_started_at'),
    )
    
    def mark_processing_started(self):
        self.status = 'processing'
        self.processing_started_at = datetime.utcnow()
        db.session.commit()
    
    def mark_processing_completed(self):
        self.status = 'completed'
        self.processing_completed_at = datetime.utcnow()
        self.processing_error = None
        db.session.commit()
    
    def mark_processing_failed(self, error_message):
        self.status = 'failed'
        self.processing_error = error_message
        self.processing_completed_at = datetime.utcnow()
        db.session.commit()
    
    def get_processing_time(self):
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None
    
    def to_dict(self, include_vectors=False):
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'thumbnail_path': self.thumbnail_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'status': self.status,
            'extracted_text': self.extracted_text,
            'image_date': self.image_date.isoformat() if self.image_date else None,
            'location': self.location,
            'exif_data': self.exif_data,
            'metadata': self.metadata,
            'processing_time': self.get_processing_time(),
            'face_count': len(self.faces),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_vectors:
            data['vector_id'] = self.vector_id
            data['embedding_version'] = self.embedding_version
        
        return data
    
    @classmethod
    def get_by_checksum(cls, checksum, user_id):
        return cls.query.filter_by(checksum=checksum, user_id=user_id).first()
    
    @classmethod
    def get_pending_processing(cls, limit=10):
        return cls.query.filter_by(status='pending').limit(limit).all()
    
    @classmethod
    def get_failed_processing(cls, limit=10):
        return cls.query.filter_by(status='failed').limit(limit).all()
    
    def __repr__(self):
        return f'<Image {self.filename} - {self.status}>'