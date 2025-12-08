"""
V2 Face Detection and Recognition API Endpoints

This module provides modern face detection and recognition endpoints using:
- MTCNN for face detection
- FaceNet512 (512-dim) for face embeddings
- pgvector for similarity search
- DBSCAN for face clustering
"""
import os
from typing import List, Optional
from flask import Blueprint, request, jsonify, send_file, current_app
from pydantic import BaseModel, Field, validator
from marshmallow import Schema, fields, validate

from extensions import db, limiter
from models.face import Face
from models.modern_image import ModernImage
from models.audit_log import AuditLog
from middleware.auth import require_auth
from services.face_service import FaceService
from tasks.face_tasks import process_faces_async, cluster_faces_async

# Initialize blueprint
faces_bp_v2 = Blueprint('faces_v2', __name__, url_prefix='/faces')
face_service = FaceService()


# ==================== Pydantic Request Models ====================

class FaceListRequest(BaseModel):
    """Request model for listing faces with filters."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = Field(default=None)
    person_id: Optional[str] = None
    cluster_id: Optional[str] = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sort_by: str = Field(default='created_at')
    sort_order: str = Field(default='desc')

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['pending', 'processed', 'clustered', 'failed']:
            raise ValueError('Invalid status')
        return v

    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v not in ['created_at', 'confidence_score', 'quality_score']:
            raise ValueError('Invalid sort_by field')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Invalid sort_order')
        return v


class PersonAssignmentRequest(BaseModel):
    """Request model for assigning faces to a person."""
    person_name: str = Field(..., min_length=1, max_length=100)
    face_ids: List[int] = Field(..., min_items=1)

    @validator('person_name')
    def validate_person_name(cls, v):
        # Remove extra whitespace
        v = ' '.join(v.split())
        if not v or len(v) < 1:
            raise ValueError('Person name cannot be empty')
        return v


# ==================== Response Schemas (Marshmallow for Swagger) ====================

class FaceResponseSchema(Schema):
    id = fields.Int()
    face_id = fields.Str()
    file_path = fields.Str()
    bounding_box = fields.Dict()
    confidence_score = fields.Float()
    face_cluster_id = fields.Str(allow_none=True)
    is_primary_face = fields.Bool()
    person_name = fields.Str(allow_none=True)
    person_id = fields.Str(allow_none=True)
    manual_verification = fields.Bool()
    quality_score = fields.Float(allow_none=True)
    age_estimate = fields.Int(allow_none=True)
    gender_estimate = fields.Str(allow_none=True)
    emotion_estimate = fields.Str(allow_none=True)
    status = fields.Str()
    image_id = fields.Int(allow_none=True)
    modern_image_id = fields.Int(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# ==================== Endpoints ====================

@faces_bp_v2.route('/', methods=['GET'])
@require_auth
@limiter.limit("200 per hour")
def list_faces(current_user):
    """
    List all faces for the current user with filtering and pagination.

    Query Parameters:
        - page (int): Page number (default: 1)
        - per_page (int): Items per page (default: 20, max: 100)
        - status (str): Filter by status (pending, processed, clustered, failed)
        - person_id (str): Filter by person ID
        - cluster_id (str): Filter by cluster ID
        - min_confidence (float): Minimum confidence score (0.0-1.0)
        - sort_by (str): Sort field (created_at, confidence_score, quality_score)
        - sort_order (str): Sort direction (asc, desc)

    Returns:
        JSON response with faces array, face_images URLs, and pagination info
    """
    try:
        # Parse and validate request
        try:
            req_data = FaceListRequest(
                page=int(request.args.get('page', 1)),
                per_page=int(request.args.get('per_page', 20)),
                status=request.args.get('status'),
                person_id=request.args.get('person_id'),
                cluster_id=request.args.get('cluster_id'),
                min_confidence=float(request.args.get('min_confidence', 0.0)),
                sort_by=request.args.get('sort_by', 'created_at'),
                sort_order=request.args.get('sort_order', 'desc')
            )
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid request parameters: {str(e)}'
            }), 400

        # Build query for modern images (pgvector-based)
        query = Face.query.filter(Face.modern_image_id.isnot(None))
        query = query.join(ModernImage, Face.modern_image_id == ModernImage.id)
        query = query.filter(ModernImage.user_id == current_user.id)

        # Apply filters
        if req_data.status:
            query = query.filter(Face.status == req_data.status)

        if req_data.person_id:
            query = query.filter(Face.person_id == req_data.person_id)

        if req_data.cluster_id:
            query = query.filter(Face.face_cluster_id == req_data.cluster_id)

        if req_data.min_confidence > 0.0:
            query = query.filter(Face.confidence_score >= req_data.min_confidence)

        # Apply sorting
        if hasattr(Face, req_data.sort_by):
            order_column = getattr(Face, req_data.sort_by)
            if req_data.sort_order == 'desc':
                order_column = order_column.desc()
            query = query.order_by(order_column)

        # Paginate
        pagination = query.paginate(
            page=req_data.page,
            per_page=req_data.per_page,
            error_out=False
        )

        # Build face_images list for frontend compatibility
        face_images = []
        for face in pagination.items:
            face_image_url = f"/api/v2/faces/{face.id}/image"
            face_images.append(face_image_url)

        return jsonify({
            'status': 'success',
            'data': {
                'faces': [face.to_dict() for face in pagination.items],
                'face_images': face_images,
                'pagination': {
                    'page': req_data.page,
                    'per_page': req_data.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"List faces error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve faces'
        }), 500


@faces_bp_v2.route('/<int:face_id>', methods=['GET'])
@require_auth
@limiter.limit("500 per hour")
def get_face(face_id, current_user):
    """Get details for a specific face by ID."""
    try:
        face = (Face.query
                .join(ModernImage, Face.modern_image_id == ModernImage.id)
                .filter(Face.id == face_id, ModernImage.user_id == current_user.id)
                .first())

        if not face:
            return jsonify({
                'status': 'error',
                'message': 'Face not found'
            }), 404

        return jsonify({
            'status': 'success',
            'data': face.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get face error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve face'
        }), 500


@faces_bp_v2.route('/<int:face_id>/image', methods=['GET'])
@require_auth
@limiter.limit("1000 per hour")
def serve_face_image(face_id, current_user):
    """Serve the face image file."""
    try:
        face = (Face.query
                .join(ModernImage, Face.modern_image_id == ModernImage.id)
                .filter(Face.id == face_id, ModernImage.user_id == current_user.id)
                .first())

        if not face:
            return jsonify({
                'status': 'error',
                'message': 'Face not found'
            }), 404

        # Build full path
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        full_face_path = os.path.join(upload_folder, face.file_path)

        if not os.path.exists(full_face_path):
            current_app.logger.error(f"Face image file not found: {full_face_path}")
            return jsonify({
                'status': 'error',
                'message': 'Face image file not found'
            }), 404

        return send_file(
            full_face_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"face_{face.face_id}.jpg"
        )

    except Exception as e:
        current_app.logger.error(f"Serve face image error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to serve face image'
        }), 500


@faces_bp_v2.route('/process', methods=['POST'])
@require_auth
@limiter.limit("10 per hour")
def trigger_face_processing(current_user):
    """Trigger face detection and processing for all completed images."""
    try:
        user_images = ModernImage.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).all()

        if not user_images:
            return jsonify({
                'status': 'success',
                'message': 'No completed images found to process',
                'data': {'processed_count': 0}
            }), 200

        image_ids = [img.id for img in user_images]
        task = process_faces_async.delay(image_ids)

        return jsonify({
            'status': 'success',
            'message': 'Face processing started for your images',
            'data': {
                'task_id': task.id,
                'images_queued': len(image_ids)
            }
        }), 202

    except Exception as e:
        current_app.logger.error(f"Face processing trigger error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start face processing'
        }), 500


@faces_bp_v2.route('/cluster', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")
def trigger_face_clustering(current_user):
    """Trigger face clustering using DBSCAN algorithm."""
    try:
        user_faces = (Face.query
                      .join(ModernImage, Face.modern_image_id == ModernImage.id)
                      .filter(ModernImage.user_id == current_user.id, Face.status == 'processed')
                      .count())

        if user_faces < 2:
            return jsonify({
                'status': 'success',
                'message': 'Not enough processed faces for clustering',
                'data': {'face_count': user_faces}
            }), 200

        task = cluster_faces_async.delay(current_user.id)

        return jsonify({
            'status': 'success',
            'message': 'Face clustering started',
            'data': {
                'task_id': task.id,
                'faces_to_cluster': user_faces
            }
        }), 202

    except Exception as e:
        current_app.logger.error(f"Face clustering trigger error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start face clustering'
        }), 500


@faces_bp_v2.route('/assign-person', methods=['POST'])
@require_auth
@limiter.limit("50 per hour")
def assign_person_to_faces(current_user):
    """Assign multiple faces to a named person."""
    try:
        # Parse and validate request
        try:
            req_data = PersonAssignmentRequest(**request.get_json())
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid request data: {str(e)}'
            }), 400

        # Verify all faces belong to user
        faces = (Face.query
                 .join(ModernImage, Face.modern_image_id == ModernImage.id)
                 .filter(Face.id.in_(req_data.face_ids), ModernImage.user_id == current_user.id)
                 .all())

        if len(faces) != len(req_data.face_ids):
            return jsonify({
                'status': 'error',
                'message': 'Some faces not found or not accessible'
            }), 404

        person_id = f"person_{req_data.person_name.lower().replace(' ', '_')}"

        updated_faces = []
        for face in faces:
            face.assign_person(req_data.person_name, person_id, manual=True)
            updated_faces.append(face.to_dict())

        AuditLog.log_resource_access(
            resource_type='face',
            resource_id=f"batch_{len(faces)}_faces",
            action='assign_person',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )

        return jsonify({
            'status': 'success',
            'message': f'Successfully assigned {len(faces)} faces to {req_data.person_name}',
            'data': {
                'person_name': req_data.person_name,
                'person_id': person_id,
                'updated_faces': updated_faces
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Assign person error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to assign person'
        }), 500


@faces_bp_v2.route('/<int:face_id>/similar', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def find_similar_faces(face_id, current_user):
    """Find similar faces using pgvector cosine similarity."""
    try:
        face = (Face.query
                .join(ModernImage, Face.modern_image_id == ModernImage.id)
                .filter(Face.id == face_id, ModernImage.user_id == current_user.id)
                .first())

        if not face:
            return jsonify({
                'status': 'error',
                'message': 'Face not found'
            }), 404

        similar_faces = face_service.find_similar_faces(
            face_id=face.id,
            user_id=current_user.id,
            similarity_threshold=0.7,
            limit=20
        )

        return jsonify({
            'status': 'success',
            'data': {
                'face_id': face_id,
                'similar_faces': [f.to_dict() for f in similar_faces],
                'total_similar': len(similar_faces)
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Find similar faces error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to find similar faces'
        }), 500


@faces_bp_v2.route('/<int:face_id>/images', methods=['GET'])
@require_auth
@limiter.limit("200 per hour")
def get_face_images(face_id, current_user):
    """Get all images containing this face or similar faces in the same cluster."""
    try:
        face = (Face.query
                .join(ModernImage, Face.modern_image_id == ModernImage.id)
                .filter(Face.id == face_id, ModernImage.user_id == current_user.id)
                .first())

        if not face:
            return jsonify({
                'status': 'error',
                'message': 'Face not found'
            }), 404

        # Get all similar faces (same cluster or find via embeddings)
        similar_face_ids = [face.id]

        if face.face_cluster_id:
            cluster_faces = Face.query.filter_by(face_cluster_id=face.face_cluster_id).all()
            similar_face_ids = [f.id for f in cluster_faces]
        else:
            similar_faces = face_service.find_similar_faces(
                face_id=face.id,
                user_id=current_user.id,
                similarity_threshold=0.6,
                limit=50
            )
            similar_face_ids.extend([f.id for f in similar_faces])

        # Get all unique images
        images_data = []
        seen_image_ids = set()

        for face_obj in Face.query.filter(Face.id.in_(similar_face_ids)).all():
            if face_obj.modern_image_id:
                modern_img = ModernImage.query.get(face_obj.modern_image_id)
                if modern_img and modern_img.user_id == current_user.id:
                    if modern_img.id not in seen_image_ids:
                        seen_image_ids.add(modern_img.id)
                        images_data.append({
                            'id': modern_img.id,
                            'filename': modern_img.filename,
                            'thumbnail_url': f"/api/v2/images/{modern_img.id}/thumbnail",
                            'full_url': f"/api/v2/images/{modern_img.id}/file",
                            'created_at': modern_img.created_at.isoformat(),
                            'face_count': Face.query.filter_by(modern_image_id=modern_img.id).count()
                        })

        return jsonify({
            'status': 'success',
            'data': {
                'face_id': face_id,
                'face_cluster_id': face.face_cluster_id,
                'person_name': face.person_name,
                'images': images_data,
                'total_images': len(images_data),
                'total_similar_faces': len(similar_face_ids)
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get face images error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve face images'
        }), 500


@faces_bp_v2.route('/stats', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def get_face_stats(current_user):
    """Get face processing statistics for the current user."""
    try:
        stats = face_service.get_user_face_stats(current_user.id)

        return jsonify({
            'status': 'success',
            'data': stats
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get face stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve face stats'
        }), 500


@faces_bp_v2.route('/clusters', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def list_face_clusters(current_user):
    """List all face clusters for the current user."""
    try:
        clusters = face_service.get_face_clusters_for_user(current_user.id)

        return jsonify({
            'status': 'success',
            'data': {
                'clusters': clusters,
                'total_clusters': len(clusters)
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"List clusters error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve clusters'
        }), 500


@faces_bp_v2.route('/persons', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def list_persons(current_user):
    """List all named persons with face counts."""
    try:
        from sqlalchemy import func

        persons = (db.session.query(
            Face.person_id,
            Face.person_name,
            func.count(Face.id).label('face_count')
        )
        .join(ModernImage, Face.modern_image_id == ModernImage.id)
        .filter(ModernImage.user_id == current_user.id, Face.person_id.isnot(None))
        .group_by(Face.person_id, Face.person_name)
        .all())

        person_data = []
        for person in persons:
            sample_faces = (Face.query
                            .join(ModernImage, Face.modern_image_id == ModernImage.id)
                            .filter(Face.person_id == person.person_id, ModernImage.user_id == current_user.id)
                            .order_by(Face.confidence_score.desc())
                            .limit(3)
                            .all())

            person_data.append({
                'person_id': person.person_id,
                'person_name': person.person_name,
                'face_count': person.face_count,
                'sample_faces': [face.to_dict() for face in sample_faces]
            })

        return jsonify({
            'status': 'success',
            'data': {
                'persons': person_data,
                'total_persons': len(person_data)
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"List persons error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve persons'
        }), 500
