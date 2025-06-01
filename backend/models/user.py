import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from config.settings import Config
from extensions import db, jwt, mail, celery, cache, limiter, bcrypt
from middleware.auth import setup_jwt_handlers
from middleware.audit_logger import setup_audit_logging
from utils.security import setup_security_headers

def create_app(config_name='default'):
    app = Flask(__name__)
    
    config_obj = Config()
    app.config.from_object(config_obj)
    
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    celery.conf.update(app.config)
    
    setup_jwt_handlers(jwt)
    setup_audit_logging(app)
    setup_security_headers(app)
    
    migrate = Migrate(app, db)
    
    from api.v1 import v1_bp
    app.register_blueprint(v1_bp, url_prefix='/api/v1')
    
    @app.route('/health')
    @limiter.exempt
    def health_check():
        try:
            db.session.execute('SELECT 1')
            cache.get('health_check')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'cache': 'connected',
                'version': '1.0.0'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    @app.route('/metrics')
    @limiter.exempt
    def metrics():
        from prometheus_client import generate_latest
        return generate_latest()
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429
    
    return app

def make_celery(app):
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

app = create_app()
celery = make_celery(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))