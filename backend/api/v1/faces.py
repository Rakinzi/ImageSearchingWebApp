from flask import Blueprint, request, jsonify, send_file, current_app
from flask_smorest import Blueprint as SmorestBlueprint
from marshmallow import Schema, fields, validate
import os
from datetime import datetime

from extensions import db, limiter
from models.face import Face
from models.image import Image
from middleware.auth import require_auth
from middleware.audit_logger import AuditLogger
from services.face_service import FaceService
from tasks.face_tasks import process_faces_async, cluster_faces_async
from utils.validators import validate_person_name, validate_confidence_score, validate_pagination

faces_bp = SmorestBlueprint('faces', __name__, description='Face detection and management operations')
face_service = FaceService()

class FaceListSchema(Schema):
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=20, validate=validate.Range(min=1, max=100))
    status = fields.Str(missing=None, validate=validate.OneOf(['pending', 'processed', 'clustered', 'failed']))
    person_id = fields.Str(missing=None)
    cluster_id = fields.Str(missing=None)
    min_confidence = fields.Float(missing=0.0, validate=validate.Range(min=0.0, max=1.0))
    sort_by = fields.Str(missing='created_at', validate=validate.OneOf(['created_at', 'confidence_score', 'quality_score']))
    sort_order = fields.Str(missing='desc', validate=validate.OneOf(['asc', 'desc']))

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
    image_id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class PersonAssignmentSchema(Schema):
    person_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    face_ids = fields.List(fields.Int(), required=True, validate=validate.Length(min=1))

class ClusterResponseSchema(Schema):
    cluster_id = fields.Str()
    face_count = fields.Int()
    primary_face = fields.Nested(FaceResponseSchema, allow_none=True)
    representative_faces = fields.List(fields.Nested(FaceResponseSchema))
    person_name = fields.Str(allow_none=True)
    confidence_range = fields.Dict()

@faces_bp.route('/process', methods=['POST'])
@require_auth
@limiter.limit("10 per hour")
def trigger_face_processing(current_user):
    try:
        user_images = Image.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).all()
        
        if not user_images:
            return jsonify({
                'message': 'No completed images found to process',
                'processed_count': 0
            }), 200
        
        image_ids = [img.id for img in user_images]
        
        task = process_faces_async.delay(image_ids)
        
        return jsonify({
            'message': 'Face processing started for your images',
            'task_id': task.id,
            'images_queued': len(image_ids)
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Face processing trigger error: {str(e)}")
        return jsonify({'error': 'Failed to start face processing'}), 500

@faces_bp.route('/', methods=['GET'])
@faces_bp.arguments(FaceListSchema, location='query')
@require_auth
@limiter.limit("200 per hour")
def list_faces(query_args, current_user):
    try:
        page = query_args.get('page', 1)
        per_page = query_args.get('per_page', 20)
        status = query_args.get('status')
        person_id = query_args.get('person_id')
        cluster_id = query_args.get('cluster_id')
        min_confidence = query_args.get('min_confidence', 0.0)
        sort_by = query_args.get('sort_by', 'created_at')
        sort_order = query_args.get('sort_order', 'desc')
        
        query = Face.query.join(Image).filter(Image.user_id == current_user.id)
        
        if status:
            query = query.filter(Face.status == status)
        
        if person_id:
            query = query.filter(Face.person_id == person_id)
        
        if cluster_id:
            query = query.filter(Face.face_cluster_id == cluster_id)
        
        if min_confidence > 0.0:
            query = query.filter(Face.confidence_score >= min_confidence)
        
        if hasattr(Face, sort_by):
            order_column = getattr(Face, sort_by)
            if sort_order == 'desc':
                order_column = order_column.desc()
            query = query.order_by(order_column)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        faces = [face.to_dict() for face in pagination.items]
        
        return jsonify({
            'faces': faces,
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
        current_app.logger.error(f"List faces error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve faces'}), 500

@faces_bp.route('/<int:face_id>', methods=['GET'])
@require_auth
@limiter.limit("500 per hour")
def get_face(face_id, current_user):
    try:
        face = Face.query.join(Image).filter(
            Face.id == face_id,
            Image.user_id == current_user.id
        ).first()
        
        if not face:
            return jsonify({'error': 'Face not found'}), 404
        
        return jsonify(face.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get face error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve face'}), 500

@faces_bp.route('/<int:face_id>/image', methods=['GET'])
@require_auth
@limiter.limit("1000 per hour")
def serve_face_image(face_id, current_user):
    try:
        face = Face.query.join(Image).filter(
            Face.id == face_id,
            Image.user_id == current_user.id
        ).first()
        
        if not face:
            return jsonify({'error': 'Face not found'}), 404
        
        if not os.path.exists(face.file_path):
            return jsonify({'error': 'Face image file not found'}), 404
        
        return send_file(
            face.file_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"face_{face.face_id}.jpg"
        )
        
    except Exception as e:
        current_app.logger.error(f"Serve face image error: {str(e)}")
        return jsonify({'error': 'Failed to serve face image'}), 500

@faces_bp.route('/clusters', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def list_face_clusters(current_user):
    try:
        from sqlalchemy import func
        
        clusters = db.session.query(
            Face.face_cluster_id,
            func.count(Face.id).label('face_count'),
            func.avg(Face.confidence_score).label('avg_confidence'),
            func.min(Face.confidence_score).label('min_confidence'),
            func.max(Face.confidence_score).label('max_confidence')
        ).join(Image).filter(
            Image.user_id == current_user.id,
            Face.face_cluster_id.isnot(None)
        ).group_by(Face.face_cluster_id).all()
        
        cluster_data = []
        for cluster in clusters:
            primary_face = Face.query.join(Image).filter(
                Face.face_cluster_id == cluster.face_cluster_id,
                Face.is_primary_face == True,
                Image.user_id == current_user.id
            ).first()
            
            representative_faces = Face.query.join(Image).filter(
                Face.face_cluster_id == cluster.face_cluster_id,
                Image.user_id == current_user.id
            ).order_by(Face.confidence_score.desc()).limit(5).all()
            
            cluster_info = {
                'cluster_id': cluster.face_cluster_id,
                'face_count': cluster.face_count,
                'primary_face': primary_face.to_dict() if primary_face else None,
                'representative_faces': [face.to_dict() for face in representative_faces],
                'person_name': primary_face.person_name if primary_face else None,
                'confidence_range': {
                    'average': float(cluster.avg_confidence),
                    'minimum': float(cluster.min_confidence),
                    'maximum': float(cluster.max_confidence)
                }
            }
            cluster_data.append(cluster_info)
        
        return jsonify({
            'clusters': cluster_data,
            'total_clusters': len(cluster_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"List clusters error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve clusters'}), 500

@faces_bp.route('/clusters/<cluster_id>/faces', methods=['GET'])
@require_auth
@limiter.limit("200 per hour")
def get_cluster_faces(cluster_id, current_user):
    try:
        faces = Face.query.join(Image).filter(
            Face.face_cluster_id == cluster_id,
            Image.user_id == current_user.id
        ).order_by(Face.confidence_score.desc()).all()
        
        if not faces:
            return jsonify({'error': 'Cluster not found or empty'}), 404
        
        return jsonify({
            'cluster_id': cluster_id,
            'faces': [face.to_dict() for face in faces],
            'total_faces': len(faces)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get cluster faces error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve cluster faces'}), 500

@faces_bp.route('/assign-person', methods=['POST'])
@faces_bp.arguments(PersonAssignmentSchema)
@require_auth
@limiter.limit("50 per hour")
def assign_person_to_faces(json_data, current_user):
    try:
        person_name = json_data['person_name'].strip()
        face_ids = json_data['face_ids']
        
        is_valid_name, validated_name = validate_person_name(person_name)
        if not is_valid_name:
            return jsonify({'error': validated_name}), 400
        
        faces = Face.query.join(Image).filter(
            Face.id.in_(face_ids),
            Image.user_id == current_user.id
        ).all()
        
        if len(faces) != len(face_ids):
            return jsonify({'error': 'Some faces not found or not accessible'}), 404
        
        person_id = f"person_{validated_name.lower().replace(' ', '_')}"
        
        updated_faces = []
        for face in faces:
            face.assign_person(validated_name, person_id, manual=True)
            updated_faces.append(face.to_dict())
        
        AuditLogger.log_resource_access(
            resource_type='face',
            resource_id=f"batch_{len(faces)}_faces",
            action='assign_person',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify({
            'message': f'Successfully assigned {len(faces)} faces to {validated_name}',
            'person_name': validated_name,
            'person_id': person_id,
            'updated_faces': updated_faces
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Assign person error: {str(e)}")
        return jsonify({'error': 'Failed to assign person'}), 500

@faces_bp.route('/persons', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def list_persons(current_user):
    try:
        from sqlalchemy import func
        
        persons = db.session.query(
            Face.person_id,
            Face.person_name,
            func.count(Face.id).label('face_count')
        ).join(Image).filter(
            Image.user_id == current_user.id,
            Face.person_id.isnot(None)
        ).group_by(Face.person_id, Face.person_name).all()
        
        person_data = []
        for person in persons:
            sample_faces = Face.query.join(Image).filter(
                Face.person_id == person.person_id,
                Image.user_id == current_user.id
            ).order_by(Face.confidence_score.desc()).limit(3).all()
            
            person_info = {
                'person_id': person.person_id,
                'person_name': person.person_name,
                'face_count': person.face_count,
                'sample_faces': [face.to_dict() for face in sample_faces]
            }
            person_data.append(person_info)
        
        return jsonify({
            'persons': person_data,
            'total_persons': len(person_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"List persons error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve persons'}), 500

@faces_bp.route('/persons/<person_id>/faces', methods=['GET'])
@require_auth
@limiter.limit("200 per hour")
def get_person_faces(person_id, current_user):
    try:
        faces = Face.query.join(Image).filter(
            Face.person_id == person_id,
            Image.user_id == current_user.id
        ).order_by(Face.confidence_score.desc()).all()
        
        if not faces:
            return jsonify({'error': 'Person not found or has no faces'}), 404
        
        return jsonify({
            'person_id': person_id,
            'person_name': faces[0].person_name,
            'faces': [face.to_dict() for face in faces],
            'total_faces': len(faces)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get person faces error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve person faces'}), 500

@faces_bp.route('/cluster', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")
def trigger_face_clustering(current_user):
    try:
        user_faces = Face.query.join(Image).filter(
            Image.user_id == current_user.id,
            Face.status == 'processed'
        ).count()
        
        if user_faces < 2:
            return jsonify({
                'message': 'Not enough processed faces for clustering',
                'face_count': user_faces
            }), 200
        
        task = cluster_faces_async.delay(current_user.id)
        
        return jsonify({
            'message': 'Face clustering started',
            'task_id': task.id,
            'faces_to_cluster': user_faces
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Face clustering trigger error: {str(e)}")
        return jsonify({'error': 'Failed to start face clustering'}), 500

@faces_bp.route('/<int:face_id>/similar', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def find_similar_faces(face_id, current_user):
    try:
        face = Face.query.join(Image).filter(
            Face.id == face_id,
            Image.user_id == current_user.id
        ).first()
        
        if not face:
            return jsonify({'error': 'Face not found'}), 404
        
        similar_faces = face_service.find_similar_faces(
            face_id=face.id,
            user_id=current_user.id,
            similarity_threshold=0.7,
            limit=20
        )
        
        return jsonify({
            'face_id': face_id,
            'similar_faces': [face_data.to_dict() for face_data in similar_faces],
            'total_similar': len(similar_faces)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Find similar faces error: {str(e)}")
        return jsonify({'error': 'Failed to find similar faces'}), 500

@faces_bp.route('/stats', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def get_face_stats(current_user):
    try:
        from sqlalchemy import func
        
        stats = db.session.query(
            Face.status,
            func.count(Face.id).label('count')
        ).join(Image).filter(
            Image.user_id == current_user.id
        ).group_by(Face.status).all()
        
        total_faces = db.session.query(
            func.count(Face.id)
        ).join(Image).filter(
            Image.user_id == current_user.id
        ).scalar() or 0
        
        unique_persons = db.session.query(
            func.count(func.distinct(Face.person_id))
        ).join(Image).filter(
            Image.user_id == current_user.id,
            Face.person_id.isnot(None)
        ).scalar() or 0
        
        total_clusters = db.session.query(
            func.count(func.distinct(Face.face_cluster_id))
        ).join(Image).filter(
            Image.user_id == current_user.id,
            Face.face_cluster_id.isnot(None)
        ).scalar() or 0
        
        status_counts = {status: count for status, count in stats}
        
        return jsonify({
            'total_faces': total_faces,
            'unique_persons': unique_persons,
            'total_clusters': total_clusters,
            'status_breakdown': status_counts,
            'processing_summary': {
                'processed': status_counts.get('processed', 0),
                'clustered': status_counts.get('clustered', 0),
                'pending': status_counts.get('pending', 0),
                'failed': status_counts.get('failed', 0)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get face stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve face stats'}), 500