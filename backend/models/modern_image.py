"""
Modern Image model with enhanced type hints, async support, and better patterns.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Dict, List, Optional, Any, ClassVar
from dataclasses import dataclass

from sqlalchemy import Index, Text, event
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from pgvector.sqlalchemy import Vector
from extensions import db
from utils.time_utils import now as harare_now


class ImageStatus(enum.Enum):
    """Image processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ImageMetrics:
    """Data class for image processing metrics."""
    processing_time: Optional[float]
    face_count: int
    text_length: int
    has_location: bool
    has_date: bool


class ModernImage(db.Model):
    """
    Modern Image model with enhanced functionality and type safety.

    This model includes:
    - Better type hints and validation
    - Async-ready patterns
    - Enhanced query methods
    - Improved data serialization
    - Built-in metrics and analytics
    """
    __tablename__ = 'modern_images'

    # Primary key and identification
    id: int = db.Column(db.Integer, primary_key=True)
    filename: str = db.Column(db.String(255), nullable=False)
    original_filename: str = db.Column(db.String(255), nullable=False)
    file_path: str = db.Column(db.String(500), nullable=False, index=True)
    thumbnail_path: Optional[str] = db.Column(db.String(500), nullable=True)

    # File properties
    file_size: int = db.Column(db.Integer, nullable=False)
    mime_type: str = db.Column(db.String(100), nullable=False)
    width: Optional[int] = db.Column(db.Integer, nullable=True)
    height: Optional[int] = db.Column(db.Integer, nullable=True)
    checksum: str = db.Column(db.String(64), nullable=False, index=True, unique=False)

    # Processing status
    status: ImageStatus = db.Column(
        db.Enum(ImageStatus),
        default=ImageStatus.PENDING,
        nullable=False,
        index=True
    )

    # Content extraction
    extracted_text: Optional[str] = db.Column(Text, nullable=True)
    image_date: Optional[datetime] = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    location: Optional[str] = db.Column(db.String(500), nullable=True)

    # Metadata
    exif_data: Optional[Dict[str, Any]] = db.Column(JSON, nullable=True)
    image_metadata: Optional[Dict[str, Any]] = db.Column(JSON, nullable=True)

    # Vector database integration
    vector_id: Optional[str] = db.Column(db.String(255), nullable=True, index=True)  # Legacy ChromaDB ID
    embedding: Optional[Any] = db.Column(Vector(768), nullable=True)  # pgvector embedding (ViT-L/14: 768-dim)
    embedding_model: str = db.Column(db.String(100), default='ViT-L-14', nullable=False)
    embedding_version: str = db.Column(db.String(50), default='v3', nullable=False)  # v3 = pgvector with ViT-L/14

    # Processing tracking
    processing_started_at: Optional[datetime] = db.Column(db.DateTime(timezone=True), nullable=True)
    processing_completed_at: Optional[datetime] = db.Column(db.DateTime(timezone=True), nullable=True)
    processing_error: Optional[str] = db.Column(Text, nullable=True)
    processing_attempts: int = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Timestamps
    created_at: datetime = db.Column(db.DateTime(timezone=True), default=harare_now, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime(timezone=True),
        default=harare_now,
        onupdate=harare_now,
        nullable=False
    )

    # Relationships
    faces = db.relationship('Face', backref='modern_image', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Face.modern_image_id')

    # Indexes for performance
    __table_args__ = (
        Index('ix_modern_images_user_status', 'user_id', 'status'),
        Index('ix_modern_images_user_created', 'user_id', 'created_at'),
        Index('ix_modern_images_checksum_user', 'checksum', 'user_id'),
        Index('ix_modern_images_location', 'location'),
        Index('ix_modern_images_processing', 'status', 'processing_started_at'),
        Index('ix_modern_images_date_location', 'image_date', 'location'),
        db.UniqueConstraint('checksum', 'user_id', name='uq_image_user_checksum'),
    )

    # Validation
    @validates('file_size')
    def validate_file_size(self, key: str, value: int) -> int:
        """Validate file size is positive."""
        if value <= 0:
            raise ValueError("File size must be positive")
        return value

    @validates('mime_type')
    def validate_mime_type(self, key: str, value: str) -> str:
        """Validate mime type format."""
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value not in allowed_types:
            raise ValueError(f"Unsupported mime type: {value}")
        return value

    # Hybrid properties
    @hybrid_property
    def is_processing(self) -> bool:
        """Check if image is currently being processed."""
        return self.status == ImageStatus.PROCESSING

    @hybrid_property
    def processing_time(self) -> Optional[float]:
        """Calculate processing time in seconds."""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

    @processing_time.expression
    def processing_time(cls):
        """SQL expression for processing time calculation (PostgreSQL compatible)."""
        return db.func.extract('epoch', cls.processing_completed_at - cls.processing_started_at)

    @hybrid_property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio."""
        if self.width and self.height:
            return self.width / self.height
        return None

    @hybrid_property
    def has_faces(self) -> bool:
        """Check if image has detected faces."""
        return self.faces.count() > 0

    # Processing state management
    def start_processing(self) -> None:
        """Mark image as processing started."""
        self.status = ImageStatus.PROCESSING
        self.processing_started_at = harare_now()
        self.processing_attempts += 1
        db.session.commit()

    def complete_processing(self) -> None:
        """Mark image processing as completed successfully."""
        self.status = ImageStatus.COMPLETED
        self.processing_completed_at = harare_now()
        self.processing_error = None
        db.session.commit()

    def fail_processing(self, error_message: str) -> None:
        """Mark image processing as failed with error message."""
        self.status = ImageStatus.FAILED
        self.processing_error = error_message
        self.processing_completed_at = harare_now()
        db.session.commit()

    def retry_processing(self) -> None:
        """Reset image for retry processing."""
        self.status = ImageStatus.PENDING
        self.processing_error = None
        self.processing_started_at = None
        self.processing_completed_at = None
        db.session.commit()

    # Query methods
    @classmethod
    def find_by_checksum(cls, checksum: str, user_id: int) -> Optional[ModernImage]:
        """Find image by checksum and user ID."""
        return cls.query.filter_by(checksum=checksum, user_id=user_id).first()

    @classmethod
    def get_pending_for_processing(cls, limit: int = 10) -> List[ModernImage]:
        """Get images pending processing."""
        return (cls.query
                .filter_by(status=ImageStatus.PENDING)
                .order_by(cls.created_at.asc())
                .limit(limit)
                .all())

    @classmethod
    def get_failed_processing(cls, max_attempts: int = 3, limit: int = 10) -> List[ModernImage]:
        """Get images that failed processing with retry limit."""
        return (cls.query
                .filter(
                    cls.status == ImageStatus.FAILED,
                    cls.processing_attempts < max_attempts
                )
                .order_by(cls.processing_completed_at.desc())
                .limit(limit)
                .all())

    @classmethod
    def get_by_user_and_status(cls, user_id: int, status: ImageStatus) -> List[ModernImage]:
        """Get user's images by status."""
        return cls.query.filter_by(user_id=user_id, status=status).all()

    @classmethod
    def get_recent_by_user(cls, user_id: int, limit: int = 20) -> List[ModernImage]:
        """Get user's most recent images."""
        return (cls.query
                .filter_by(user_id=user_id)
                .order_by(cls.created_at.desc())
                .limit(limit)
                .all())

    @classmethod
    def search_by_location(cls, location_query: str, user_id: Optional[int] = None) -> List[ModernImage]:
        """Search images by location."""
        query = cls.query.filter(cls.location.like(f'%{location_query}%'))
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.all()

    @classmethod
    def search_by_text(cls, text_query: str, user_id: Optional[int] = None) -> List[ModernImage]:
        """Search images by extracted text."""
        query = cls.query.filter(cls.extracted_text.like(f'%{text_query}%'))
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.all()

    @classmethod
    def search_by_embedding(cls, query_embedding: List[float],
                          user_id: Optional[int] = None,
                          limit: int = 20,
                          similarity_threshold: float = 0.7) -> List[tuple['ModernImage', float]]:
        """
        Search images by vector similarity using pgvector.

        Args:
            query_embedding: Query vector (768-dim for ViT-L/14)
            user_id: Optional user ID filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1, higher = stricter)

        Returns:
            List of tuples (image, similarity_score) sorted by similarity
        """
        from sqlalchemy import func

        # pgvector cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity: 1 - (distance / 2) => 1 = identical, 0 = opposite
        distance = cls.embedding.cosine_distance(query_embedding)
        similarity = (1 - (distance / 2)).label('similarity')

        query = (db.session.query(cls, similarity)
                .filter(cls.embedding.isnot(None))
                .filter(cls.status == ImageStatus.COMPLETED))

        if user_id:
            query = query.filter_by(user_id=user_id)

        # Filter by similarity threshold
        # distance threshold = 2 * (1 - similarity_threshold)
        distance_threshold = 2 * (1 - similarity_threshold)
        query = query.filter(distance < distance_threshold)

        # Order by similarity (descending) and limit
        query = query.order_by(distance.asc()).limit(limit)

        results = []
        for image, sim in query.all():
            results.append((image, float(sim)))

        return results

    # Analytics and metrics
    def get_metrics(self) -> ImageMetrics:
        """Get image processing metrics."""
        return ImageMetrics(
            processing_time=self.processing_time,
            face_count=self.faces.count(),
            text_length=len(self.extracted_text or ''),
            has_location=bool(self.location),
            has_date=bool(self.image_date)
        )

    @classmethod
    def get_user_statistics(cls, user_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a user's images."""
        total_images = cls.query.filter_by(user_id=user_id).count()

        status_counts = {}
        for status in ImageStatus:
            count = cls.query.filter_by(user_id=user_id, status=status).count()
            status_counts[status.value] = count

        # Calculate average processing time using database-agnostic approach
        completed_images = cls.query.filter_by(
            user_id=user_id,
            status=ImageStatus.COMPLETED
        ).filter(
            cls.processing_started_at.isnot(None),
            cls.processing_completed_at.isnot(None)
        ).all()

        avg_processing_time = 0.0
        if completed_images:
            total_processing_time = sum(
                (img.processing_completed_at - img.processing_started_at).total_seconds()
                for img in completed_images
            )
            avg_processing_time = total_processing_time / len(completed_images)

        total_file_size = (db.session.query(db.func.sum(cls.file_size))
                          .filter_by(user_id=user_id).scalar() or 0)

        return {
            'total_images': total_images,
            'status_breakdown': status_counts,
            'avg_processing_time_seconds': float(avg_processing_time),
            'total_file_size_bytes': total_file_size,
            'images_with_faces': cls.query.filter_by(user_id=user_id).filter(cls.faces.any()).count(),
            'images_with_location': cls.query.filter_by(user_id=user_id).filter(cls.location.isnot(None)).count(),
            'images_with_text': cls.query.filter_by(user_id=user_id).filter(cls.extracted_text.isnot(None)).count(),
        }

    # Serialization
    def to_dict(self, include_sensitive: bool = False, include_metrics: bool = False) -> Dict[str, Any]:
        """
        Convert image to dictionary with configurable detail level.

        Args:
            include_sensitive: Include processing details and vector IDs
            include_metrics: Include computed metrics
        """
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
            'status': self.status.value,
            'extracted_text': self.extracted_text,
            'image_date': self.image_date.isoformat() if self.image_date else None,
            'location': self.location,
            'exif_data': self.exif_data,
            'metadata': self.image_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if include_sensitive:
            data.update({
                'vector_id': self.vector_id,
                'embedding_version': self.embedding_version,
                'processing_started_at': (
                    self.processing_started_at.isoformat()
                    if self.processing_started_at else None
                ),
                'processing_completed_at': (
                    self.processing_completed_at.isoformat()
                    if self.processing_completed_at else None
                ),
                'processing_error': self.processing_error,
                'processing_attempts': self.processing_attempts,
            })

        if include_metrics:
            metrics = self.get_metrics()
            data['metrics'] = {
                'processing_time': metrics.processing_time,
                'face_count': metrics.face_count,
                'text_length': metrics.text_length,
                'has_location': metrics.has_location,
                'has_date': metrics.has_date,
                'aspect_ratio': self.aspect_ratio,
            }

        return data

    def __repr__(self) -> str:
        return f'<ModernImage(id={self.id}, filename="{self.filename}", status={self.status.value})>'


# Event listeners for automatic updates
@event.listens_for(ModernImage, 'before_update')
def update_timestamp(mapper, connection, target):
    """Automatically update the updated_at timestamp."""
    target.updated_at = harare_now()


@event.listens_for(ModernImage, 'after_insert')
def log_image_creation(mapper, connection, target):
    """Log image creation for audit purposes."""
    # Could integrate with audit logging system
    pass


@event.listens_for(ModernImage, 'after_update')
def log_status_changes(mapper, connection, target):
    """Log important status changes."""
    # Could integrate with audit logging system
    pass
