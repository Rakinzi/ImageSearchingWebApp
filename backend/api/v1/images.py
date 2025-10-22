from flask import Blueprint, request, jsonify, send_file, current_app
from flask_smorest import Blueprint as SmorestBlueprint
from marshmallow import Schema, fields, validate
from werkzeug.datastructures import FileStorage
import os
from datetime import datetime

from extensions import db, limiter
from models.image import Image
from models.user import User
from middleware.auth import require_auth, optional_auth
from middleware.audit_logger import AuditLogger
from services.image_service import ImageService
from tasks.image_tasks import process_image_async, batch_process_images_async
from utils.validators import validate_image_file, validate_search_query, validate_pagination
from utils.helpers import validate_and_process_image
from utils.security import generate_secure_filename, calculate_file_hash

images_bp = SmorestBlueprint('images', __name__, description='Image management operations')
image_service = ImageService()

class ImageUploadSchema(Schema):
    files = fields.List(fields.Raw(), required=True, validate=validate.Length(min=1, max=10))
    metadata = fields.Dict(load_default={})

class ImageSearchSchema(Schema):
    query = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    limit = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    similarity_threshold = fields.Float(load_default=0.85, validate=validate.Range(min=0.0, max=1.0))
    include_metadata = fields.Bool(load_default=False)

class ImageListSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    status = fields.Str(load_default=None, validate=validate.OneOf(['pending', 'processing', 'completed', 'failed']))
    sort_by = fields.Str(load_default='created_at', validate=validate.OneOf(['created_at', 'updated_at', 'file_size', 'image_date']))
    sort_order = fields.Str(load_default='desc', validate=validate.OneOf(['asc', 'desc']))
    start_date = fields.DateTime(load_default=None)
    end_date = fields.DateTime(load_default=None)

class ImageResponseSchema(Schema):
    id = fields.Int()
    filename = fields.Str()
    original_filename = fields.Str()
    file_path = fields.Str()
    thumbnail_path = fields.Str()
    file_size = fields.Int()
    mime_type = fields.Str()
    width = fields.Int()
    height = fields.Int()
    status = fields.Str()
    image_date = fields.DateTime(allow_none=True)
    location = fields.Str(allow_none=True)
    face_count = fields.Int()
    processing_time = fields.Float(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class BatchUploadResponseSchema(Schema):
    successful_uploads = fields.List(fields.Nested(ImageResponseSchema))
    failed_uploads = fields.List(fields.Dict())
    total_processed = fields.Int()
    total_successful = fields.Int()
    total_failed = fields.Int()

@images_bp.route('/upload', methods=['POST'])
@require_auth
@limiter.limit("20 per hour")
def upload_images(current_user):
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed per upload'}), 400
        
        successful_uploads = []
        failed_uploads = []
        
        for file in files:
            try:
                if not file.filename:
                    failed_uploads.append({
                        'filename': 'unknown',
                        'error': 'No filename provided'
                    })
                    continue
                
                is_valid, error_message = validate_image_file(file)
                if not is_valid:
                    failed_uploads.append({
                        'filename': file.filename,
                        'error': error_message
                    })
                    continue
                
                file_data = file.read()
                file.seek(0)
                
                checksum = calculate_file_hash(file_data)
                existing_image = Image.get_by_checksum(checksum, current_user.id)
                
                if existing_image:
                    failed_uploads.append({
                        'filename': file.filename,
                        'error': 'Duplicate image already exists',
                        'existing_image_id': existing_image.id
                    })
                    continue
                
                secure_filename = generate_secure_filename(file.filename)
                
                upload_paths = image_service.create_user_directories(current_user.id)
                image_path = os.path.join(upload_paths['images'], secure_filename)
                
                with open(image_path, 'wb') as f:
                    f.write(file_data)
                
                try:
                    processed_data = validate_and_process_image(file_data, file.filename)
                    
                    thumbnail_filename = f"thumb_{secure_filename}"
                    thumbnail_path = os.path.join(upload_paths['thumbnails'], thumbnail_filename)
                    
                    with open(thumbnail_path, 'wb') as f:
                        f.write(processed_data['thumbnail_data'])
                    
                    image = Image(
                        filename=secure_filename,
                        original_filename=file.filename,
                        file_path=image_path,
                        thumbnail_path=thumbnail_path,
                        file_size=processed_data['file_size'],
                        mime_type=file.content_type or f"image/{processed_data['format'].lower()}",
                        width=processed_data['width'],
                        height=processed_data['height'],
                        checksum=processed_data['checksum'],
                        image_date=processed_data['image_date'],
                        location=processed_data['location_data']['address'] if processed_data['location_data'] else None,
                        exif_data=processed_data['exif_data'],
                        metadata={
                            'location_data': processed_data['location_data'],
                            'latitude': processed_data['latitude'],
                            'longitude': processed_data['longitude']
                        },
                        user_id=current_user.id
                    )
                    
                    db.session.add(image)
                    db.session.commit()
                    
                    process_image_async.delay(image.id)
                    
                    AuditLogger.log_image_upload(
                        user_id=current_user.id,
                        image_id=image.id,
                        filename=file.filename,
                        ip_address=request.remote_addr,
                        success=True
                    )
                    
                    successful_uploads.append(image.to_dict())
                    
                except Exception as processing_error:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    failed_uploads.append({
                        'filename': file.filename,
                        'error': f'Processing failed: {str(processing_error)}'
                    })
                    
            except Exception as file_error:
                failed_uploads.append({
                    'filename': getattr(file, 'filename', 'unknown'),
                    'error': str(file_error)
                })
        
        response_data = {
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'total_processed': len(files),
            'total_successful': len(successful_uploads),
            'total_failed': len(failed_uploads)
        }
        
        status_code = 201 if successful_uploads else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@images_bp.route('/search', methods=['POST'])
@images_bp.arguments(ImageSearchSchema)
@require_auth
@limiter.limit("100 per hour")
def search_images(json_data, current_user):
    try:
        query = json_data['query']
        limit = json_data.get('limit', 20)
        similarity_threshold = json_data.get('similarity_threshold', 0.85)
        include_metadata = json_data.get('include_metadata', False)
        
        is_valid_query, sanitized_query = validate_search_query(query)
        if not is_valid_query:
            return jsonify({'error': sanitized_query}), 400
        
        results = image_service.search_images(
            query=sanitized_query,
            user_id=current_user.id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        if not results:
            return jsonify({
                'message': 'No images match your search query',
                'results': [],
                'total_count': 0
            }), 200
        
        image_ids = [result['id'] for result in results]
        images = Image.query.filter(
            Image.id.in_(image_ids),
            Image.user_id == current_user.id
        ).all()
        
        response_images = []
        for image in images:
            image_data = image.to_dict()
            if include_metadata:
                image_data['metadata'] = image.metadata
                image_data['exif_data'] = image.exif_data
            response_images.append(image_data)
        
        AuditLogger.log_image_search(
            user_id=current_user.id,
            query=sanitized_query,
            result_count=len(response_images),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'results': response_images,
            'total_count': len(response_images),
            'query': sanitized_query,
            'similarity_threshold': similarity_threshold
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@images_bp.route('/', methods=['GET'])
@images_bp.arguments(ImageListSchema, location='query')
@require_auth
@limiter.limit("200 per hour")
def list_images(query_args, current_user):
    try:
        page = query_args.get('page', 1)
        per_page = query_args.get('per_page', 20)
        status = query_args.get('status')
        sort_by = query_args.get('sort_by', 'created_at')
        sort_order = query_args.get('sort_order', 'desc')
        start_date = query_args.get('start_date')
        end_date = query_args.get('end_date')
        
        query = Image.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            query = query.filter(Image.created_at >= start_date)
        
        if end_date:
            query = query.filter(Image.created_at <= end_date)
        
        if hasattr(Image, sort_by):
            order_column = getattr(Image, sort_by)
            if sort_order == 'desc':
                order_column = order_column.desc()
            query = query.order_by(order_column)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        images = [image.to_dict() for image in pagination.items]
        
        return jsonify({
            'images': images,
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
        current_app.logger.error(f"List images error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve images'}), 500

@images_bp.route('/<int:image_id>', methods=['GET'])
@require_auth
@limiter.limit("500 per hour")
def get_image(image_id, current_user):
    try:
        image = Image.query.filter_by(id=image_id, user_id=current_user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify(image.to_dict(include_vectors=False)), 200
        
    except Exception as e:
        current_app.logger.error(f"Get image error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve image'}), 500

@images_bp.route('/<int:image_id>/file', methods=['GET'])
@optional_auth
@limiter.limit("1000 per hour")
def serve_image_file(image_id, current_user):
    try:
        # If user is authenticated, verify they own the image
        if current_user:
            image = Image.query.filter_by(id=image_id, user_id=current_user.id).first()
        else:
            # Allow unauthenticated access (browser img tags)
            # You might want to restrict this based on your security requirements
            image = Image.query.filter_by(id=image_id).first()

        if not image:
            return jsonify({'error': 'Image not found'}), 404

        if not os.path.exists(image.file_path):
            return jsonify({'error': 'Image file not found on disk'}), 404

        return send_file(
            image.file_path,
            mimetype=image.mime_type,
            as_attachment=False,
            download_name=image.original_filename
        )

    except Exception as e:
        current_app.logger.error(f"Serve image error: {str(e)}")
        return jsonify({'error': 'Failed to serve image'}), 500

@images_bp.route('/<int:image_id>/thumbnail', methods=['GET'])
@optional_auth
@limiter.limit("2000 per hour")
def serve_thumbnail(image_id, current_user):
    try:
        # If user is authenticated, verify they own the image
        if current_user:
            image = Image.query.filter_by(id=image_id, user_id=current_user.id).first()
        else:
            # Allow unauthenticated access (browser img tags)
            image = Image.query.filter_by(id=image_id).first()

        if not image:
            return jsonify({'error': 'Image not found'}), 404

        if not image.thumbnail_path or not os.path.exists(image.thumbnail_path):
            return jsonify({'error': 'Thumbnail not found'}), 404

        return send_file(
            image.thumbnail_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"thumb_{image.original_filename}"
        )

    except Exception as e:
        current_app.logger.error(f"Serve thumbnail error: {str(e)}")
        return jsonify({'error': 'Failed to serve thumbnail'}), 500

@images_bp.route('/<int:image_id>', methods=['DELETE'])
@require_auth
@limiter.limit("50 per hour")
def delete_image(image_id, current_user):
    try:
        image = Image.query.filter_by(id=image_id, user_id=current_user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        try:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
            
            if image.thumbnail_path and os.path.exists(image.thumbnail_path):
                os.remove(image.thumbnail_path)
            
            image_service.remove_from_vector_db(image.vector_id)
            
        except Exception as cleanup_error:
            current_app.logger.warning(f"Cleanup error for image {image_id}: {str(cleanup_error)}")
        
        db.session.delete(image)
        db.session.commit()
        
        AuditLogger.log_resource_access(
            resource_type='image',
            resource_id=image_id,
            action='delete',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete image error: {str(e)}")
        return jsonify({'error': 'Failed to delete image'}), 500

@images_bp.route('/batch-upload', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")
def batch_upload_images(current_user):
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if len(files) > 50:
            return jsonify({'error': 'Maximum 50 files allowed for batch upload'}), 400
        
        batch_process_images_async.delay(
            user_id=current_user.id,
            file_data=[{
                'filename': file.filename,
                'data': file.read(),
                'content_type': file.content_type
            } for file in files]
        )
        
        return jsonify({
            'message': 'Batch upload started. You will be notified when processing is complete.',
            'total_files': len(files)
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Batch upload error: {str(e)}")
        return jsonify({'error': 'Batch upload failed'}), 500

@images_bp.route('/reprocess/<int:image_id>', methods=['POST'])
@require_auth
@limiter.limit("10 per hour")
def reprocess_image(image_id, current_user):
    try:
        image = Image.query.filter_by(id=image_id, user_id=current_user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        if image.status == 'processing':
            return jsonify({'error': 'Image is already being processed'}), 409
        
        image.status = 'pending'
        image.processing_error = None
        db.session.commit()
        
        process_image_async.delay(image.id)
        
        return jsonify({
            'message': 'Image reprocessing started',
            'image_id': image_id
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Reprocess image error: {str(e)}")
        return jsonify({'error': 'Failed to reprocess image'}), 500

@images_bp.route('/stats', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def get_image_stats(current_user):
    try:
        from sqlalchemy import func
        
        stats = db.session.query(
            Image.status,
            func.count(Image.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Image.status).all()
        
        total_size = db.session.query(
            func.sum(Image.file_size)
        ).filter_by(user_id=current_user.id).scalar() or 0
        
        total_images = db.session.query(
            func.count(Image.id)
        ).filter_by(user_id=current_user.id).scalar() or 0
        
        status_counts = {status: count for status, count in stats}
        
        return jsonify({
            'total_images': total_images,
            'total_size_bytes': total_size,
            'total_size_formatted': image_service.format_file_size(total_size),
            'status_breakdown': status_counts,
            'processing_summary': {
                'completed': status_counts.get('completed', 0),
                'pending': status_counts.get('pending', 0),
                'processing': status_counts.get('processing', 0),
                'failed': status_counts.get('failed', 0)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve stats'}), 500