import os
import cv2
import numpy as np
import torch
import logging
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from io import BytesIO
from PIL import Image as PILImage

from facenet_pytorch import MTCNN
DEEPFACE_HOME = os.getenv("DEEPFACE_HOME")
if not DEEPFACE_HOME:
    DEEPFACE_HOME = os.path.join(
        os.getenv("HOME", "/tmp"),
        ".deepface"
    )
    os.environ.setdefault("DEEPFACE_HOME", DEEPFACE_HOME)

try:
    os.makedirs(DEEPFACE_HOME, exist_ok=True)
except PermissionError:
    fallback_home = "/tmp/.deepface"
    os.environ["DEEPFACE_HOME"] = fallback_home
    os.makedirs(fallback_home, exist_ok=True)

from deepface import DeepFace
from sklearn.cluster import DBSCAN
from flask import current_app

from models.face import Face
from models.image import Image
from services.vector_service import VectorService
from utils.helpers import generate_unique_id
from utils.security import generate_secure_filename
from extensions import db

logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self):
        self.device = self._get_optimal_device()
        self.mtcnn = None
        self.vector_service = VectorService()
        self.face_detection_threshold = None
        self.face_similarity_threshold = None
        self.faces_dir = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure the service is initialized with Flask app context"""
        if not self._initialized:
            self.face_detection_threshold = current_app.config.get('FACE_DETECTION_THRESHOLD', 0.99)
            self.face_similarity_threshold = current_app.config.get('FACE_SIMILARITY_THRESHOLD', 0.55)
            self.faces_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'faces')
            self._initialize_face_detector()
            self._initialized = True
    
    def _get_optimal_device(self):
        if torch.cuda.is_available():
            logger.info("Using CUDA device for face processing")
            return torch.device('cuda')
        else:
            logger.info("Using CPU device for face processing")
            return torch.device('cpu')
    
    def _initialize_face_detector(self):
        try:
            self.mtcnn = MTCNN(
                keep_all=True,
                device=self.device,
                min_face_size=20,
                thresholds=[0.6, 0.7, 0.8],
                factor=0.709,
                post_process=True
            )
            logger.info("MTCNN face detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {str(e)}")
            raise Exception(f"Face detector initialization failed: {str(e)}")
    
    def detect_faces_in_image(self, image_id: int) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        try:
            image = Image.query.get(image_id)
            if not image or not os.path.exists(image.file_path):
                logger.error(f"Image {image_id} not found or file missing")
                return []
            
            cv_image = cv2.imread(image.file_path)
            if cv_image is None:
                logger.error(f"Could not load image file: {image.file_path}")
                return []
            
            image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            boxes, probs, landmarks = self.mtcnn.detect(image_rgb, landmarks=True)
            
            detected_faces = []
            
            if boxes is not None and len(boxes) > 0:
                for i, (box, prob, landmark) in enumerate(zip(boxes, probs, landmarks)):
                    if prob > self.face_detection_threshold:
                        face_data = self._extract_face_region(
                            image_rgb, box, image_id, i, prob, landmark
                        )
                        if face_data:
                            detected_faces.append(face_data)
            
            logger.info(f"Detected {len(detected_faces)} faces in image {image_id}")
            return detected_faces
            
        except Exception as e:
            logger.error(f"Face detection failed for image {image_id}: {str(e)}")
            return []
    
    def _extract_face_region(self, image_rgb: np.ndarray, box: np.ndarray, 
                           image_id: int, face_index: int, confidence: float,
                           landmarks: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        try:
            x1, y1, x2, y2 = map(int, box)
            height, width = image_rgb.shape[:2]
            
            expand_ratio = 0.3
            new_x1 = max(0, int(x1 - (x2 - x1) * expand_ratio))
            new_y1 = max(0, int(y1 - (y2 - y1) * expand_ratio))
            new_x2 = min(width, int(x2 + (x2 - x1) * expand_ratio))
            new_y2 = min(height, int(y2 + (y2 - y1) * expand_ratio * 1.5))
            
            face_region = image_rgb[new_y1:new_y2, new_x1:new_x2]
            
            if face_region.size == 0:
                return None
            
            face_id = generate_unique_id(f'face_{image_id}_{face_index}_')
            face_filename = f"{face_id}.jpg"
            
            user_id = Image.query.get(image_id).user_id
            face_dir = os.path.join(self.faces_dir, str(user_id))
            os.makedirs(face_dir, exist_ok=True)
            
            face_path = os.path.join(face_dir, face_filename)
            
            face_bgr = cv2.cvtColor(face_region, cv2.COLOR_RGB2BGR)
            cv2.imwrite(face_path, face_bgr)
            
            quality_score = self._calculate_face_quality(face_region)
            
            bounding_box = {
                'x1': float(x1), 'y1': float(y1),
                'x2': float(x2), 'y2': float(y2),
                'expanded_x1': float(new_x1), 'expanded_y1': float(new_y1),
                'expanded_x2': float(new_x2), 'expanded_y2': float(new_y2)
            }
            
            if landmarks is not None:
                bounding_box['landmarks'] = landmarks.tolist()
            
            return {
                'face_id': face_id,
                'file_path': face_path,
                'bounding_box': bounding_box,
                'confidence_score': float(confidence),
                'quality_score': quality_score,
                'image_id': image_id
            }
            
        except Exception as e:
            logger.error(f"Face extraction failed: {str(e)}")
            return None
    
    def _calculate_face_quality(self, face_region: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
            
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            height, width = face_region.shape[:2]
            size_score = min(1.0, (height * width) / (100 * 100))
            
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            quality = (laplacian_var / 1000 + size_score + brightness_score) / 3
            return min(1.0, max(0.0, quality))
            
        except Exception as e:
            logger.warning(f"Quality calculation failed: {str(e)}")
            return 0.5
    
    def generate_face_embedding(self, face_path: str) -> Optional[np.ndarray]:
        try:
            if not os.path.exists(face_path):
                return None
            
            embedding = DeepFace.represent(
                face_path,
                model_name="Facenet512",
                enforce_detection=False,
                detector_backend='opencv'
            )[0]['embedding']
            
            return np.array(embedding)
            
        except Exception as e:
            logger.error(f"Face embedding generation failed: {str(e)}")
            return None
    
    def analyze_face_attributes(self, face_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(face_path):
                return {}
            
            analysis = DeepFace.analyze(
                face_path,
                actions=['age', 'gender', 'emotion'],
                enforce_detection=False,
                detector_backend='opencv'
            )[0]
            
            return {
                'age_estimate': int(analysis.get('age', 0)),
                'gender_estimate': analysis.get('dominant_gender', 'unknown').lower(),
                'emotion_estimate': analysis.get('dominant_emotion', 'unknown').lower(),
                'emotion_scores': analysis.get('emotion', {}),
                'gender_confidence': analysis.get('gender', {}).get(analysis.get('dominant_gender', ''), 0)
            }
            
        except Exception as e:
            logger.warning(f"Face attribute analysis failed: {str(e)}")
            return {
                'age_estimate': None,
                'gender_estimate': 'unknown',
                'emotion_estimate': 'unknown'
            }
    
    def process_image_faces(self, image_id: int) -> Dict[str, Any]:
        self._ensure_initialized()
        try:
            detected_faces = self.detect_faces_in_image(image_id)
            
            results = {
                'image_id': image_id,
                'faces_detected': len(detected_faces),
                'faces_processed': 0,
                'faces_failed': 0,
                'face_ids': []
            }
            
            for face_data in detected_faces:
                try:
                    face = Face(
                        face_id=face_data['face_id'],
                        file_path=face_data['file_path'],
                        checksum=self._calculate_face_checksum(face_data['file_path']),
                        bounding_box=face_data['bounding_box'],
                        confidence_score=face_data['confidence_score'],
                        quality_score=face_data['quality_score'],
                        image_id=image_id,
                        status='pending'
                    )
                    
                    db.session.add(face)
                    db.session.commit()
                    
                    embedding = self.generate_face_embedding(face_data['file_path'])
                    if embedding is not None:
                        face.set_embedding(embedding)
                        
                        attributes = self.analyze_face_attributes(face_data['file_path'])
                        face.age_estimate = attributes.get('age_estimate')
                        face.gender_estimate = attributes.get('gender_estimate')
                        face.emotion_estimate = attributes.get('emotion_estimate')
                        
                        metadata = {
                            'image_id': image_id,
                            'face_id': face.face_id,
                            'confidence_score': face.confidence_score,
                            'quality_score': face.quality_score,
                            'age_estimate': face.age_estimate,
                            'gender_estimate': face.gender_estimate,
                            'emotion_estimate': face.emotion_estimate
                        }
                        
                        if self.vector_service.store_face_vector(face.face_id, embedding, metadata):
                            face.mark_processed()
                            results['faces_processed'] += 1
                            results['face_ids'].append(face.id)
                        else:
                            face.mark_failed("Failed to store face embedding")
                            results['faces_failed'] += 1
                    else:
                        face.mark_failed("Failed to generate face embedding")
                        results['faces_failed'] += 1
                        
                except Exception as face_error:
                    logger.error(f"Failed to process face: {str(face_error)}")
                    results['faces_failed'] += 1
                    db.session.rollback()
            
            return results
            
        except Exception as e:
            logger.error(f"Face processing failed for image {image_id}: {str(e)}")
            return {
                'image_id': image_id,
                'faces_detected': 0,
                'faces_processed': 0,
                'faces_failed': 0,
                'face_ids': [],
                'error': str(e)
            }
    
    def _calculate_face_checksum(self, face_path: str) -> str:
        try:
            with open(face_path, 'rb') as f:
                import hashlib
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return generate_unique_id('checksum_')
    
    def cluster_user_faces(self, user_id: int) -> Dict[str, Any]:
        try:
            faces = Face.query.join(Image).filter(
                Image.user_id == user_id,
                Face.status == 'processed',
                Face.embedding_vector.isnot(None)
            ).all()
            
            if len(faces) < 2:
                return {
                    'user_id': user_id,
                    'total_faces': len(faces),
                    'clusters_created': 0,
                    'faces_clustered': 0,
                    'message': 'Not enough faces for clustering'
                }
            
            embeddings = []
            face_ids = []
            
            for face in faces:
                embedding = face.get_embedding()
                if embedding is not None:
                    embeddings.append(embedding)
                    face_ids.append(face.id)
            
            if len(embeddings) < 2:
                return {
                    'user_id': user_id,
                    'total_faces': len(faces),
                    'clusters_created': 0,
                    'faces_clustered': 0,
                    'message': 'Not enough valid embeddings for clustering'
                }
            
            embeddings_array = np.array(embeddings)
            
            clustering = DBSCAN(
                eps=1 - self.face_similarity_threshold,
                min_samples=1,
                metric='cosine'
            ).fit(embeddings_array)
            
            cluster_labels = clustering.labels_
            unique_clusters = set(cluster_labels)
            unique_clusters.discard(-1)  # Remove noise points
            
            clusters_created = 0
            faces_clustered = 0
            
            for cluster_id in unique_clusters:
                cluster_faces = [
                    face_ids[i] for i, label in enumerate(cluster_labels) 
                    if label == cluster_id
                ]
                
                if len(cluster_faces) > 0:
                    cluster_uuid = f"cluster_{user_id}_{cluster_id}_{generate_unique_id()}"
                    
                    primary_face_id = self._select_primary_face(cluster_faces)
                    
                    for face_id in cluster_faces:
                        face = Face.query.get(face_id)
                        if face:
                            face.mark_clustered(
                                cluster_uuid, 
                                is_primary=(face_id == primary_face_id)
                            )
                            faces_clustered += 1
                    
                    clusters_created += 1
            
            return {
                'user_id': user_id,
                'total_faces': len(faces),
                'processed_faces': len(embeddings),
                'clusters_created': clusters_created,
                'faces_clustered': faces_clustered,
                'noise_points': list(cluster_labels).count(-1)
            }
            
        except Exception as e:
            logger.error(f"Face clustering failed for user {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'total_faces': 0,
                'clusters_created': 0,
                'faces_clustered': 0,
                'error': str(e)
            }
    
    def _select_primary_face(self, face_ids: List[int]) -> int:
        try:
            faces = Face.query.filter(Face.id.in_(face_ids)).all()
            
            best_face = max(faces, key=lambda f: (
                f.quality_score or 0,
                f.confidence_score or 0
            ))
            
            return best_face.id
            
        except Exception:
            return face_ids[0] if face_ids else None
    
    def find_similar_faces(self, face_id: int, user_id: int, 
                          similarity_threshold: float = 0.7, 
                          limit: int = 20) -> List[Face]:
        try:
            face = Face.query.join(Image).filter(
                Face.id == face_id,
                Image.user_id == user_id
            ).first()
            
            if not face or not face.embedding_vector:
                return []
            
            query_embedding = face.get_embedding()
            if query_embedding is None:
                return []
            
            filter_metadata = {'user_id': user_id}
            
            similar_results = self.vector_service.search_similar_faces(
                query_embedding=query_embedding,
                limit=limit + 1,
                similarity_threshold=similarity_threshold,
                filter_metadata=filter_metadata
            )
            
            similar_faces = []
            for result in similar_results:
                try:
                    result_face_id = result['id']
                    if result_face_id == face.face_id:
                        continue
                    
                    similar_face = Face.query.filter_by(face_id=result_face_id).first()
                    if similar_face:
                        similar_faces.append(similar_face)
                        
                except Exception as e:
                    logger.warning(f"Error processing similar face result: {str(e)}")
                    continue
            
            return similar_faces[:limit]
            
        except Exception as e:
            logger.error(f"Find similar faces failed: {str(e)}")
            return []
    
    def get_face_clusters_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            from sqlalchemy import func
            
            cluster_data = db.session.query(
                Face.face_cluster_id,
                func.count(Face.id).label('face_count'),
                func.avg(Face.confidence_score).label('avg_confidence'),
                func.max(Face.quality_score).label('max_quality')
            ).join(Image).filter(
                Image.user_id == user_id,
                Face.face_cluster_id.isnot(None)
            ).group_by(Face.face_cluster_id).all()
            
            clusters = []
            for cluster_id, face_count, avg_confidence, max_quality in cluster_data:
                primary_face = Face.query.join(Image).filter(
                    Face.face_cluster_id == cluster_id,
                    Face.is_primary_face == True,
                    Image.user_id == user_id
                ).first()
                
                sample_faces = Face.query.join(Image).filter(
                    Face.face_cluster_id == cluster_id,
                    Image.user_id == user_id
                ).order_by(Face.quality_score.desc()).limit(5).all()
                
                cluster_info = {
                    'cluster_id': cluster_id,
                    'face_count': face_count,
                    'avg_confidence': float(avg_confidence) if avg_confidence else 0.0,
                    'max_quality': float(max_quality) if max_quality else 0.0,
                    'primary_face': primary_face.to_dict() if primary_face else None,
                    'sample_faces': [face.to_dict() for face in sample_faces],
                    'person_name': primary_face.person_name if primary_face else None
                }
                clusters.append(cluster_info)
            
            return sorted(clusters, key=lambda x: x['face_count'], reverse=True)
            
        except Exception as e:
            logger.error(f"Get face clusters failed: {str(e)}")
            return []
    
    def assign_person_to_cluster(self, cluster_id: str, person_name: str, 
                               user_id: int, manual: bool = True) -> Dict[str, Any]:
        try:
            faces = Face.query.join(Image).filter(
                Face.face_cluster_id == cluster_id,
                Image.user_id == user_id
            ).all()
            
            if not faces:
                return {
                    'success': False,
                    'message': 'Cluster not found or empty',
                    'faces_updated': 0
                }
            
            person_id = f"person_{person_name.lower().replace(' ', '_')}"
            
            updated_count = 0
            for face in faces:
                face.assign_person(person_name, person_id, manual)
                updated_count += 1
            
            return {
                'success': True,
                'message': f'Assigned {updated_count} faces to {person_name}',
                'faces_updated': updated_count,
                'person_id': person_id,
                'cluster_id': cluster_id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Assign person to cluster failed: {str(e)}")
            return {
                'success': False,
                'message': f'Assignment failed: {str(e)}',
                'faces_updated': 0
            }
    
    def get_user_face_stats(self, user_id: int) -> Dict[str, Any]:
        try:
            from sqlalchemy import func
            
            total_faces = Face.query.join(Image).filter(
                Image.user_id == user_id
            ).count()
            
            status_stats = db.session.query(
                Face.status,
                func.count(Face.id).label('count')
            ).join(Image).filter(
                Image.user_id == user_id
            ).group_by(Face.status).all()
            
            unique_persons = db.session.query(
                func.count(func.distinct(Face.person_id))
            ).join(Image).filter(
                Image.user_id == user_id,
                Face.person_id.isnot(None)
            ).scalar() or 0
            
            unique_clusters = db.session.query(
                func.count(func.distinct(Face.face_cluster_id))
            ).join(Image).filter(
                Image.user_id == user_id,
                Face.face_cluster_id.isnot(None)
            ).scalar() or 0
            
            avg_confidence = db.session.query(
                func.avg(Face.confidence_score)
            ).join(Image).filter(
                Image.user_id == user_id
            ).scalar() or 0
            
            status_breakdown = {status: count for status, count in status_stats}
            
            return {
                'total_faces': total_faces,
                'unique_persons': unique_persons,
                'unique_clusters': unique_clusters,
                'average_confidence': float(avg_confidence),
                'status_breakdown': status_breakdown,
                'processing_health': {
                    'processed': status_breakdown.get('processed', 0),
                    'clustered': status_breakdown.get('clustered', 0),
                    'pending': status_breakdown.get('pending', 0),
                    'failed': status_breakdown.get('failed', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Get user face stats failed: {str(e)}")
            return {
                'total_faces': 0,
                'unique_persons': 0,
                'unique_clusters': 0,
                'average_confidence': 0.0,
                'status_breakdown': {},
                'processing_health': {
                    'processed': 0, 'clustered': 0, 'pending': 0, 'failed': 0
                }
            }
    
    def cleanup_orphaned_faces(self, user_id: Optional[int] = None) -> Dict[str, int]:
        try:
            query = Face.query.join(Image)
            if user_id:
                query = query.filter(Image.user_id == user_id)
            
            faces = query.all()
            
            cleaned_faces = 0
            cleaned_files = 0
            
            for face in faces:
                if not os.path.exists(face.file_path):
                    if face.face_id:
                        self.vector_service.remove_face_vector(face.face_id)
                    db.session.delete(face)
                    cleaned_faces += 1
                    cleaned_files += 1
            
            db.session.commit()
            
            return {
                'cleaned_faces': cleaned_faces,
                'cleaned_files': cleaned_files
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Face cleanup failed: {str(e)}")
            return {'cleaned_faces': 0, 'cleaned_files': 0}
    
    def health_check(self) -> Dict[str, Any]:
        self._ensure_initialized()
        try:
            detector_healthy = self.mtcnn is not None
            vector_service_health = self.vector_service.health_check()
            
            faces_dir_writable = os.access(self.faces_dir, os.W_OK) if os.path.exists(self.faces_dir) else False
            
            total_faces = Face.query.count()
            processing_faces = Face.query.filter_by(status='pending').count()
            failed_faces = Face.query.filter_by(status='failed').count()
            
            return {
                'healthy': (
                    detector_healthy and 
                    vector_service_health.get('healthy', False) and 
                    faces_dir_writable
                ),
                'face_detector': {
                    'loaded': detector_healthy,
                    'device': str(self.device)
                },
                'vector_service': vector_service_health,
                'storage': {
                    'faces_directory_writable': faces_dir_writable,
                    'faces_directory': self.faces_dir
                },
                'processing_stats': {
                    'total_faces': total_faces,
                    'pending_processing': processing_faces,
                    'failed_processing': failed_faces,
                    'processing_healthy': failed_faces < total_faces * 0.05
                }
            }
            
        except Exception as e:
            logger.error(f"Face service health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e)
            }
