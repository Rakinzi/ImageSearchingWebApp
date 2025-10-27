"""
Modern Images API endpoint with enhanced functionality and patterns.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from flask import request, current_app, Blueprint as FlaskBlueprint, send_file, jsonify
from flask_smorest import Blueprint, abort
from flask_smorest.fields import Upload
from marshmallow import Schema, fields, validate, post_load
from werkzeug.datastructures import FileStorage
import structlog
import os

from extensions import db, limiter
from middleware.auth import require_auth, optional_auth
from models.modern_image import ModernImage, ImageStatus
from services.modern_image_service import ModernImageService
from utils.responses import ApiResponse, ErrorResponse, PaginatedResponse, create_response, create_error_response
from utils.validators import validate_image_file, validate_pagination
from tasks.image_tasks import process_image_async

logger = structlog.get_logger(__name__)

# Create a plain Flask Blueprint for file upload (flask-smorest doesn't handle multipart well)
upload_bp = FlaskBlueprint('image_upload', __name__)

# Create flask-smorest Blueprint for other endpoints
modern_images_bp = Blueprint(
    'modern_images',
    __name__,
    description='Modern image management with enhanced functionality'
)

# Initialize service
image_service = ModernImageService()


# Request/Response Schemas
class ImageUploadRequestSchema(Schema):
    """Schema for image upload requests with files and form data."""
    files = fields.List(
        Upload(),
        required=True,
        validate=validate.Length(min=1, max=10),
        metadata={'description': 'Image files to upload (max 10)'}
    )
    extract_text = fields.Bool(
        load_default=True,
        metadata={'description': 'Whether to extract text from images'}
    )
    detect_faces = fields.Bool(
        load_default=True,
        metadata={'description': 'Whether to detect faces in images'}
    )
    generate_embeddings = fields.Bool(
        load_default=True,
        metadata={'description': 'Whether to generate vector embeddings'}
    )
    metadata = fields.Str(
        load_default="{}",
        metadata={'description': 'Additional metadata as JSON string'}
    )



class ImageSearchRequestSchema(Schema):
    """Schema for image search requests."""
    query = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        metadata={'description': 'Search query (text or image description)'}
    )
    search_type = fields.Str(
        load_default='semantic',
        validate=validate.OneOf(['semantic', 'text', 'metadata', 'hybrid']),
        metadata={'description': 'Type of search to perform'}
    )
    limit = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100),
        metadata={'description': 'Maximum number of results'}
    )
    similarity_threshold = fields.Float(
        load_default=0.8,
        validate=validate.Range(min=0.0, max=1.0),
        metadata={'description': 'Minimum similarity score'}
    )
    filters = fields.Dict(
        load_default={},
        metadata={'description': 'Additional filters (location, date range, etc.)'}
    )


class ImageListRequestSchema(Schema):
    """Schema for listing images with pagination and filtering."""
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    status = fields.Str(
        load_default=None,
        validate=validate.OneOf([s.value for s in ImageStatus] + [None])
    )
    sort_by = fields.Str(
        load_default='created_at',
        validate=validate.OneOf(['created_at', 'updated_at', 'file_size', 'image_date', 'processing_time'])
    )
    sort_order = fields.Str(
        load_default='desc',
        validate=validate.OneOf(['asc', 'desc'])
    )
    start_date = fields.DateTime(load_default=None)
    end_date = fields.DateTime(load_default=None)
    has_faces = fields.Bool(load_default=None)
    has_location = fields.Bool(load_default=None)
    has_text = fields.Bool(load_default=None)


class ImageResponseSchema(Schema):
    """Schema for image response data."""
    id = fields.Int()
    filename = fields.Str()
    original_filename = fields.Str()
    file_path = fields.Str()
    thumbnail_path = fields.Str(allow_none=True)
    file_size = fields.Int()
    mime_type = fields.Str()
    width = fields.Int(allow_none=True)
    height = fields.Int(allow_none=True)
    status = fields.Str()
    extracted_text = fields.Str(allow_none=True)
    image_date = fields.DateTime(allow_none=True)
    location = fields.Str(allow_none=True)
    exif_data = fields.Dict(allow_none=True)
    metadata = fields.Dict(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    metrics = fields.Dict(load_default={})


class ImageStatsResponseSchema(Schema):
    """Schema for image statistics response."""
    total_images = fields.Int()
    status_breakdown = fields.Dict()
    avg_processing_time_seconds = fields.Float()
    total_file_size_bytes = fields.Int()
    images_with_faces = fields.Int()
    images_with_location = fields.Int()
    images_with_text = fields.Int()


# API Endpoints

# Upload endpoint using plain Flask Blueprint (flask-smorest can't handle multipart/form-data well)
@upload_bp.route('/', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")
def upload_images(current_user):
    """
    Upload and process multiple images with modern async processing.

    This endpoint supports:
    - Multiple file upload (up to 10 files)
    - Configurable processing options
    - Async background processing
    - Comprehensive error handling
    """
    try:
        # Validate files exist
        if 'files' not in request.files:
            return create_error_response(
                error="NoFilesProvided",
                message="No files provided in request",
                status_code=400
            )

        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return create_error_response(
                error="NoFilesSelected",
                message="No files selected for upload",
                status_code=400
            )

        if len(files) > 10:
            return create_error_response(
                error="TooManyFiles",
                message="Maximum 10 files allowed per upload",
                status_code=400
            )

        logger.info("Image upload initiated",
                    user_id=current_user.id,
                    file_count=len(files))

        # Parse form data
        import json
        extract_text = request.form.get('extract_text', 'true').lower() == 'true'
        detect_faces = request.form.get('detect_faces', 'true').lower() == 'true'
        generate_embeddings = request.form.get('generate_embeddings', 'true').lower() == 'true'

        # Parse metadata from JSON string
        metadata = {}
        try:
            metadata_str = request.form.get('metadata', '{}')
            metadata = json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

        # Process uploaded files
        uploaded_images = []
        for file in files:
            if not isinstance(file, FileStorage) or not file.filename:
                continue

            # Create image record
            image = image_service.create_image_record(
                file=file,
                user_id=current_user.id,
                metadata=metadata
            )

            if image:
                uploaded_images.append(image)

                # Queue async processing with custom options
                process_image_async.delay(
                    image.id,
                    extract_text=extract_text,
                    detect_faces=detect_faces,
                    generate_embeddings=generate_embeddings
                )

        if not uploaded_images:
            return create_error_response(
                error="NoValidFiles",
                message="No valid image files were uploaded",
                status_code=400
            )

        logger.info("Images uploaded successfully",
                   user_id=current_user.id,
                   uploaded_count=len(uploaded_images))

        # Convert to response format
        response_data = [
            image.to_dict(include_metrics=True)
            for image in uploaded_images
        ]

        return create_response(
            data=response_data,
            message=f"Successfully uploaded {len(uploaded_images)} images",
            status_code=201
        )

    except Exception as e:
        logger.error("Image upload failed",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)

        return create_error_response(
            error="UploadFailed",
            message="Failed to upload images",
            status_code=500,
            details={'error': str(e)} if current_app.debug else None
        )


@modern_images_bp.route('/', methods=['GET'])
@modern_images_bp.arguments(ImageListRequestSchema, location='query')
@modern_images_bp.response(200, ImageResponseSchema(many=True))
@require_auth
@limiter.limit("100 per minute")
def list_images(query_params: Dict[str, Any], current_user):
    """
    List user's images with advanced filtering and pagination.

    Supports filtering by:
    - Processing status
    - Date ranges
    - Content features (faces, location, text)
    - Custom sorting options
    """

    try:
        # Build query
        query = ModernImage.query.filter_by(user_id=current_user.id)

        # Apply filters
        if query_params.get('status'):
            status = ImageStatus(query_params['status'])
            query = query.filter_by(status=status)

        if query_params.get('start_date'):
            query = query.filter(ModernImage.created_at >= query_params['start_date'])

        if query_params.get('end_date'):
            query = query.filter(ModernImage.created_at <= query_params['end_date'])

        if query_params.get('has_faces') is not None:
            if query_params['has_faces']:
                query = query.filter(ModernImage.faces.any())
            else:
                query = query.filter(~ModernImage.faces.any())

        if query_params.get('has_location') is not None:
            if query_params['has_location']:
                query = query.filter(ModernImage.location.isnot(None))
            else:
                query = query.filter(ModernImage.location.is_(None))

        if query_params.get('has_text') is not None:
            if query_params['has_text']:
                query = query.filter(ModernImage.extracted_text.isnot(None))
            else:
                query = query.filter(ModernImage.extracted_text.is_(None))

        # Apply sorting
        sort_field = getattr(ModernImage, query_params.get('sort_by', 'created_at'))
        if query_params.get('sort_order', 'desc') == 'desc':
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Paginate
        page = query_params.get('page', 1)
        per_page = query_params.get('per_page', 20)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Convert to response format
        images_data = [
            image.to_dict(include_metrics=True)
            for image in pagination.items
        ]

        # Create paginated response
        paginated_response = PaginatedResponse.from_pagination(pagination, images_data)

        return create_response(
            data=paginated_response.to_dict(),
            message=f"Retrieved {len(images_data)} images"
        )

    except Exception as e:
        logger.error("Failed to list images",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)

        return create_error_response(
            error="ListFailed",
            message="Failed to retrieve images",
            status_code=500
        )


@modern_images_bp.route('/search', methods=['POST'])
@modern_images_bp.arguments(ImageSearchRequestSchema)
@modern_images_bp.response(200, ImageResponseSchema(many=True))
@require_auth
@limiter.limit("30 per minute")
def search_images(search_data: Dict[str, Any], current_user):
    """
    Advanced image search with multiple search types and AI-powered similarity.

    Search types:
    - semantic: AI-powered semantic similarity search
    - text: Search extracted text content
    - metadata: Search image metadata and EXIF data
    - hybrid: Combined search across all types
    """

    try:
        search_results = image_service.search_images(
            query=search_data['query'],
            user_id=current_user.id,
            search_type=search_data.get('search_type', 'semantic'),
            limit=search_data.get('limit', 20),
            similarity_threshold=search_data.get('similarity_threshold', 0.8),
            filters=search_data.get('filters', {})
        )

        logger.info("Image search completed",
                   user_id=current_user.id,
                   query=search_data['query'],
                   search_type=search_data.get('search_type'),
                   results_count=len(search_results))

        # Convert to response format
        response_data = [
            {**image.to_dict(include_metrics=True), 'similarity_score': score}
            for image, score in search_results
        ]

        return create_response(
            data=response_data,
            message=f"Found {len(response_data)} matching images"
        )

    except Exception as e:
        logger.error("Image search failed",
                    user_id=current_user.id,
                    query=search_data.get('query'),
                    error=str(e),
                    error_type=type(e).__name__)

        return create_error_response(
            error="SearchFailed",
            message="Failed to search images",
            status_code=500
        )


@upload_bp.route('/test-search', methods=['POST'])
@limiter.limit("100 per minute")
def test_search_images():
    """
    Public test endpoint for image search - NO AUTHENTICATION REQUIRED.

    Test your image search functionality without auth.

    Request body (JSON):
    {
        "query": "your search query",
        "search_type": "semantic|text|metadata|hybrid",
        "limit": 20,
        "similarity_threshold": 0.3
    }

    Returns images with similarity scores and full URLs for testing.
    """
    try:
        # Parse request
        from flask import request
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'error': 'MissingQuery',
                'message': 'Query parameter is required',
                'example': {
                    'query': 'tea cup',
                    'search_type': 'semantic',
                    'limit': 20,
                    'similarity_threshold': 0.3
                }
            }), 400

        query = data['query']
        search_type = data.get('search_type', 'semantic')
        limit = data.get('limit', 20)
        similarity_threshold = data.get('similarity_threshold', 0.3)

        logger.info("Test search initiated",
                   query=query,
                   search_type=search_type)

        # Get all users' images for testing (you can limit to specific test user if needed)
        # For now, we'll search across all images
        from models.modern_image import ModernImage

        if search_type == 'semantic':
            # Semantic search across all users
            from services.vector_service import VectorService
            vector_service = VectorService()

            # Use text_to_image_search which handles everything
            similar_results = vector_service.text_to_image_search(
                query,
                limit=limit * 2,  # Get more to filter
                similarity_threshold=similarity_threshold
            )

            # Get corresponding images
            results = []
            for result in similar_results:
                vector_id = result['id']
                similarity = result['similarity']

                image = ModernImage.query.filter_by(
                    vector_id=vector_id,
                    status=ImageStatus.COMPLETED
                ).first()

                if image:
                    results.append({
                        'id': image.id,
                        'filename': image.filename,
                        'original_filename': image.original_filename,
                        'similarity_score': float(similarity),
                        'created_at': image.created_at.isoformat() if image.created_at else None,
                        'file_size': image.file_size,
                        'width': image.width,
                        'height': image.height,
                        'location': image.location,
                        'extracted_text': image.extracted_text[:100] + '...' if image.extracted_text and len(image.extracted_text) > 100 else image.extracted_text,
                        'thumbnail_url': f'/api/v2/images/{image.id}/thumbnail',
                        'image_url': f'/api/v2/images/{image.id}/file'
                    })

                    if len(results) >= limit:
                        break

        elif search_type == 'text':
            # Text search (OCR)
            images = ModernImage.query.filter(
                ModernImage.extracted_text.like(f'%{query}%'),
                ModernImage.status == ImageStatus.COMPLETED
            ).limit(limit).all()

            results = [{
                'id': img.id,
                'filename': img.filename,
                'original_filename': img.original_filename,
                'similarity_score': 1.0,
                'created_at': img.created_at.isoformat() if img.created_at else None,
                'file_size': img.file_size,
                'width': img.width,
                'height': img.height,
                'location': img.location,
                'extracted_text': img.extracted_text[:100] + '...' if img.extracted_text and len(img.extracted_text) > 100 else img.extracted_text,
                'thumbnail_url': f'/api/v2/images/{img.id}/thumbnail',
                'image_url': f'/api/v2/images/{img.id}/file'
            } for img in images]

        elif search_type == 'metadata':
            # Metadata search
            images = ModernImage.query.filter(
                db.or_(
                    ModernImage.filename.like(f'%{query}%'),
                    ModernImage.original_filename.like(f'%{query}%'),
                    ModernImage.location.like(f'%{query}%')
                ),
                ModernImage.status == ImageStatus.COMPLETED
            ).limit(limit).all()

            results = [{
                'id': img.id,
                'filename': img.filename,
                'original_filename': img.original_filename,
                'similarity_score': 1.0,
                'created_at': img.created_at.isoformat() if img.created_at else None,
                'file_size': img.file_size,
                'width': img.width,
                'height': img.height,
                'location': img.location,
                'extracted_text': img.extracted_text[:100] + '...' if img.extracted_text and len(img.extracted_text) > 100 else img.extracted_text,
                'thumbnail_url': f'/api/v2/images/{img.id}/thumbnail',
                'image_url': f'/api/v2/images/{img.id}/file'
            } for img in images]

        else:
            return jsonify({
                'error': 'InvalidSearchType',
                'message': f'Invalid search type: {search_type}',
                'valid_types': ['semantic', 'text', 'metadata']
            }), 400

        logger.info("Test search completed",
                   query=query,
                   search_type=search_type,
                   results_count=len(results))

        return jsonify({
            'status': 'success',
            'query': query,
            'search_type': search_type,
            'similarity_threshold': similarity_threshold,
            'results_count': len(results),
            'data': results,
            'message': f'Found {len(results)} matching images',
            'note': 'This is a public test endpoint. Use authenticated /search for production.'
        }), 200

    except Exception as e:
        logger.error("Test search failed",
                    query=data.get('query') if 'data' in locals() else None,
                    error=str(e),
                    error_type=type(e).__name__)

        return jsonify({
            'error': 'SearchFailed',
            'message': str(e),
            'type': type(e).__name__
        }), 500


@modern_images_bp.route('/<int:image_id>', methods=['GET'])
@modern_images_bp.response(200, ImageResponseSchema)
@require_auth
@limiter.limit("100 per minute")
def get_image(image_id: int, current_user):
    """Get detailed information about a specific image."""

    image = ModernImage.query.filter_by(id=image_id, user_id=current_user.id).first()
    if not image:
        return create_error_response(
            error="ImageNotFound",
            message="Image not found",
            status_code=404
        )

    return create_response(
        data=image.to_dict(include_sensitive=True, include_metrics=True),
        message="Image retrieved successfully"
    )


@modern_images_bp.route('/<int:image_id>', methods=['DELETE'])
@modern_images_bp.response(204)
@require_auth
@limiter.limit("50 per minute")
def delete_image(image_id: int, current_user):
    """Delete an image and all associated data."""

    image = ModernImage.query.filter_by(id=image_id, user_id=current_user.id).first()
    if not image:
        return create_error_response(
            error="ImageNotFound",
            message="Image not found",
            status_code=404
        )

    try:
        image_service.delete_image(image)

        logger.info("Image deleted successfully",
                   user_id=current_user.id,
                   image_id=image_id,
                   filename=image.filename)

        return '', 204

    except Exception as e:
        logger.error("Failed to delete image",
                    user_id=current_user.id,
                    image_id=image_id,
                    error=str(e))

        return create_error_response(
            error="DeleteFailed",
            message="Failed to delete image",
            status_code=500
        )


@modern_images_bp.route('/stats', methods=['GET'])
@modern_images_bp.response(200, ImageStatsResponseSchema)
@require_auth
@limiter.limit("20 per minute")
def get_user_statistics(current_user):
    """Get comprehensive statistics about user's images."""

    try:
        stats = ModernImage.get_user_statistics(current_user.id)

        return create_response(
            data=stats,
            message="Statistics retrieved successfully"
        )

    except Exception as e:
        logger.error("Failed to get user statistics",
                    user_id=current_user.id,
                    error=str(e))

        return create_error_response(
            error="StatsFailed",
            message="Failed to retrieve statistics",
            status_code=500
        )


@modern_images_bp.route('/<int:image_id>/reprocess', methods=['POST'])
@modern_images_bp.response(202)
@require_auth
@limiter.limit("10 per minute")
def reprocess_image(image_id: int, current_user):
    """Reprocess an image (useful for failed or updated processing logic)."""

    image = ModernImage.query.filter_by(id=image_id, user_id=current_user.id).first()
    if not image:
        return create_error_response(
            error="ImageNotFound",
            message="Image not found",
            status_code=404
        )

    try:
        # Reset for reprocessing
        image.retry_processing()

        # Queue async processing with all options enabled for reprocessing
        process_image_async.delay(
            image.id,
            extract_text=True,
            detect_faces=True,
            generate_embeddings=True
        )

        logger.info("Image reprocessing queued",
                   user_id=current_user.id,
                   image_id=image_id)

        return create_response(
            message="Image queued for reprocessing",
            status_code=202
        )

    except Exception as e:
        logger.error("Failed to queue image reprocessing",
                    user_id=current_user.id,
                    image_id=image_id,
                    error=str(e))

        return create_error_response(
            error="ReprocessFailed",
            message="Failed to queue reprocessing",
            status_code=500
        )


# File serving endpoints (using plain Flask Blueprint to avoid auth issues with img tags)
@upload_bp.route('/<int:image_id>/file', methods=['GET'])
@optional_auth
@limiter.limit("1000 per hour")
def serve_image_file(image_id: int, current_user):
    """Serve the actual image file. Supports optional authentication for browser img tags."""
    try:
        # If user is authenticated, verify they own the image
        if current_user:
            image = ModernImage.query.filter_by(id=image_id, user_id=current_user.id).first()
        else:
            # Allow unauthenticated access for browser img tags
            image = ModernImage.query.filter_by(id=image_id).first()

        if not image:
            return jsonify({'error': 'Image not found'}), 404

        # Build full path
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_dir, image.file_path)

        if not os.path.exists(full_path):
            logger.error("Image file not found on disk",
                        image_id=image_id,
                        file_path=full_path)
            return jsonify({'error': 'Image file not found on disk'}), 404

        return send_file(
            full_path,
            mimetype=image.mime_type,
            as_attachment=False,
            download_name=image.original_filename
        )

    except Exception as e:
        logger.error("Serve image error",
                    image_id=image_id,
                    error=str(e))
        return jsonify({'error': 'Failed to serve image'}), 500


@upload_bp.route('/<int:image_id>/thumbnail', methods=['GET'])
@optional_auth
@limiter.limit("2000 per hour")
def serve_thumbnail(image_id: int, current_user):
    """Serve the thumbnail image. Supports optional authentication for browser img tags."""
    try:
        # If user is authenticated, verify they own the image
        if current_user:
            image = ModernImage.query.filter_by(id=image_id, user_id=current_user.id).first()
        else:
            # Allow unauthenticated access for browser img tags
            image = ModernImage.query.filter_by(id=image_id).first()

        if not image:
            return jsonify({'error': 'Image not found'}), 404

        if not image.thumbnail_path:
            return jsonify({'error': 'Thumbnail not found'}), 404

        # Build full path
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_dir, image.thumbnail_path)

        if not os.path.exists(full_path):
            logger.error("Thumbnail file not found on disk",
                        image_id=image_id,
                        file_path=full_path)
            return jsonify({'error': 'Thumbnail file not found on disk'}), 404

        return send_file(
            full_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"thumb_{image.original_filename}"
        )

    except Exception as e:
        logger.error("Serve thumbnail error",
                    image_id=image_id,
                    error=str(e))
        return jsonify({'error': 'Failed to serve thumbnail'}), 500