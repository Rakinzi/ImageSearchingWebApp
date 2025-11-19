"""
Modern API v2 with enhanced patterns and functionality.
"""
from flask import Blueprint
from flask_smorest import Api

v2_bp = Blueprint('api_v2', __name__)

def init_v2_api_docs(app):
    """Initialize API documentation for v2."""
    app.config['API_TITLE'] = 'Image Search API v2'
    app.config['API_VERSION'] = 'v2'
    app.config['OPENAPI_VERSION'] = '3.0.3'
    app.config['OPENAPI_URL_PREFIX'] = '/api/v2'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/docs'
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    app.config['OPENAPI_REDOC_PATH'] = '/redoc'
    app.config['OPENAPI_REDOC_URL'] = 'https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js'

    api = Api(app)
    return api

# Import blueprints
from .modern_images import modern_images_bp, upload_bp
from .faces import faces_bp_v2

# Register blueprints
# Upload blueprint uses plain Flask to handle multipart/form-data
v2_bp.register_blueprint(upload_bp, url_prefix='/images')
# Other image endpoints use flask-smorest for API docs
v2_bp.register_blueprint(modern_images_bp, url_prefix='/images')
# Face detection and recognition endpoints
v2_bp.register_blueprint(faces_bp_v2)