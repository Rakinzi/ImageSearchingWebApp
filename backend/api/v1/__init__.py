from flask import Blueprint
from flask_smorest import Api

v1_bp = Blueprint('api_v1', __name__)

def init_api_docs(app):
    app.config['API_TITLE'] = 'Image Search API'
    app.config['API_VERSION'] = 'v1'
    app.config['OPENAPI_VERSION'] = '3.0.2'
    app.config['OPENAPI_URL_PREFIX'] = '/api/v1'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/docs'
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    app.config['OPENAPI_REDOC_PATH'] = '/redoc'
    app.config['OPENAPI_REDOC_URL'] = 'https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js'
    
    api = Api(app)
    return api

from .auth import auth_bp
from .images import images_bp
from .faces import faces_bp
from .admin import admin_bp

v1_bp.register_blueprint(auth_bp, url_prefix='/auth')
v1_bp.register_blueprint(images_bp, url_prefix='/images')
v1_bp.register_blueprint(faces_bp, url_prefix='/faces')
v1_bp.register_blueprint(admin_bp, url_prefix='/admin')