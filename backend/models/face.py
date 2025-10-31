from typing import List, Optional, Tuple

from sqlalchemy import Index, Text
from sqlalchemy.dialects.mysql import JSON
from pgvector.sqlalchemy import Vector

from extensions import db
from utils.time_utils import now as harare_now

class Face(db.Model):
    __tablename__ = 'faces'
    
    id = db.Column(db.Integer, primary_key=True)
    face_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    file_path = db.Column(db.String(500), nullable=False)
    checksum = db.Column(db.String(64), nullable=False, index=True)
    
    bounding_box = db.Column(JSON, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    
    embedding_vector = db.Column(Text, nullable=True)
    embedding = db.Column(Vector(512), nullable=True)
    embedding_version = db.Column(db.String(50), default='v1', nullable=False)
    
    face_cluster_id = db.Column(db.String(100), nullable=True, index=True)
    is_primary_face = db.Column(db.Boolean, default=False, nullable=False)
    
    person_name = db.Column(db.String(255), nullable=True)
    person_id = db.Column(db.String(100), nullable=True, index=True)
    manual_verification = db.Column(db.Boolean, default=False, nullable=False)
    
    quality_score = db.Column(db.Float, nullable=True)
    age_estimate = db.Column(db.Integer, nullable=True)
    gender_estimate = db.Column(db.Enum('male', 'female', 'unknown', name='gender_type'), nullable=True)
    emotion_estimate = db.Column(db.String(50), nullable=True)
    
    status = db.Column(db.Enum('pending', 'processed', 'clustered', 'failed', name='face_status'), 
                      default='pending', nullable=False, index=True)
    
    processing_error = db.Column(Text, nullable=True)
    
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=True, index=True)
    modern_image_id = db.Column(db.Integer, db.ForeignKey('modern_images.id'), nullable=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=harare_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=harare_now, onupdate=harare_now, nullable=False)
    
    similar_faces = db.relationship(
        'Face',
        secondary='face_similarities',
        primaryjoin='Face.id == face_similarities.c.face_id_1',
        secondaryjoin='Face.id == face_similarities.c.face_id_2',
        backref='similar_to',
        lazy='dynamic'
    )
    
    __table_args__ = (
        Index('ix_faces_image_status', 'image_id', 'status'),
        Index('ix_faces_cluster_primary', 'face_cluster_id', 'is_primary_face'),
        Index('ix_faces_person', 'person_id', 'manual_verification'),
        Index('ix_faces_confidence', 'confidence_score'),
        Index('ix_faces_quality', 'quality_score'),
        Index('ix_faces_created_at', 'created_at'),
    )
    
    def set_embedding(self, embedding_array):
        import json
        import numpy as np

        if isinstance(embedding_array, np.ndarray):
            embedding_list = embedding_array.astype(float).tolist()
        else:
            embedding_list = [float(x) for x in embedding_array]

        self.embedding_vector = json.dumps(embedding_list)
        self.embedding = embedding_list
        self.embedding_version = 'v2_pgvector'
    
    def get_embedding(self):
        import json
        import numpy as np
        if self.embedding is not None:
            return np.array(self.embedding, dtype=np.float32)
        if self.embedding_vector:
            return np.array(json.loads(self.embedding_vector), dtype=np.float32)
        return None
    
    def mark_processed(self):
        self.status = 'processed'
        db.session.commit()
    
    def mark_clustered(self, cluster_id, is_primary=False):
        self.status = 'clustered'
        self.face_cluster_id = cluster_id
        self.is_primary_face = is_primary
        db.session.commit()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.processing_error = error_message
        db.session.commit()
    
    def assign_person(self, person_name, person_id=None, manual=True):
        self.person_name = person_name
        self.person_id = person_id or f"person_{person_name.lower().replace(' ', '_')}"
        self.manual_verification = manual
        db.session.commit()
    
    def to_dict(self, include_embedding=False):
        data = {
            'id': self.id,
            'face_id': self.face_id,
            'file_path': self.file_path,
            'bounding_box': self.bounding_box,
            'confidence_score': self.confidence_score,
            'face_cluster_id': self.face_cluster_id,
            'is_primary_face': self.is_primary_face,
            'person_name': self.person_name,
            'person_id': self.person_id,
            'manual_verification': self.manual_verification,
            'quality_score': self.quality_score,
            'age_estimate': self.age_estimate,
            'gender_estimate': self.gender_estimate,
            'emotion_estimate': self.emotion_estimate,
            'status': self.status,
            'image_id': self.image_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_embedding:
            embedding = self.get_embedding()
            if embedding is not None:
                data['embedding_vector'] = embedding.tolist()
        
        return data
    
    @classmethod
    def get_by_cluster(cls, cluster_id):
        return cls.query.filter_by(face_cluster_id=cluster_id).all()
    
    @classmethod
    def get_primary_faces(cls):
        return cls.query.filter_by(is_primary_face=True).all()
    
    @classmethod
    def get_pending_processing(cls, limit=50):
        return cls.query.filter_by(status='pending').limit(limit).all()
    
    @classmethod
    def get_by_person(cls, person_id):
        return cls.query.filter_by(person_id=person_id).all()
    
    @classmethod
    def search_by_embedding(cls,
                            query_embedding: List[float],
                            user_id: Optional[int] = None,
                            limit: int = 20,
                            similarity_threshold: float = 0.7) -> List[Tuple['Face', float]]:
        """
        Search faces by pgvector cosine similarity.

        Args:
            query_embedding: 512-dim FaceNet embedding
            user_id: Optional filter for user (supports legacy and modern images)
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1, higher = stricter)

        Returns:
            List of (Face, similarity) tuples sorted by similarity descending.
        """
        from sqlalchemy import and_, or_
        from models.modern_image import ModernImage
        from models.image import Image

        distance = cls.embedding.cosine_distance(query_embedding)
        similarity = (1 - (distance / 2)).label('similarity')

        query = (db.session.query(cls, similarity)
                 .filter(cls.embedding.isnot(None)))

        if user_id is not None:
            query = (query.outerjoin(ModernImage, cls.modern_image_id == ModernImage.id)
                          .outerjoin(Image, cls.image_id == Image.id)
                          .filter(
                              or_(
                                  and_(ModernImage.id.isnot(None), ModernImage.user_id == user_id),
                                  and_(Image.id.isnot(None), Image.user_id == user_id)
                              )
                          ))

        distance_threshold = 2 * (1 - similarity_threshold)
        query = query.filter(distance < distance_threshold)

        query = query.order_by(distance.asc()).limit(limit)

        results: List[Tuple['Face', float]] = []
        for face, sim in query.all():
            results.append((face, float(sim)))

        return results
    
    def __repr__(self):
        return f'<Face {self.face_id} - {self.status}>'

face_similarities = db.Table(
    'face_similarities',
    db.Column('face_id_1', db.Integer, db.ForeignKey('faces.id'), primary_key=True),
    db.Column('face_id_2', db.Integer, db.ForeignKey('faces.id'), primary_key=True),
    db.Column('similarity_score', db.Float, nullable=False),
    db.Column('created_at', db.DateTime(timezone=True), default=harare_now),
    Index('ix_face_similarities_score', 'similarity_score'),
    Index('ix_face_similarities_created', 'created_at')
)
