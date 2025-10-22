import os
import sys
from typing import Optional
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import text
from werkzeug.exceptions import HTTPException
import structlog

from config.settings import Config
from extensions import db, jwt, mail, celery, cache, limiter, bcrypt
from middleware.auth import setup_jwt_handlers
from middleware.audit_logger import setup_audit_logging
from utils.security import setup_security_headers
from utils.responses import ApiResponse, ErrorResponse

def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    
    config_obj = Config()
    app.config.from_object(config_obj)
    
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    # Configure limiter with Redis storage to avoid in-memory warning
    from extensions import create_limiter
    global limiter
    limiter = create_limiter(app)
    limiter.init_app(app)

    celery.conf.update(app.config)
    
    setup_jwt_handlers(jwt)
    setup_audit_logging(app)
    setup_security_headers(app)
    
    migrate = Migrate(app, db)
    
    from api.v1 import v1_bp
    from api.v2 import v2_bp
    app.register_blueprint(v1_bp, url_prefix='/api/v1')
    app.register_blueprint(v2_bp, url_prefix='/api/v2')
    
    @app.route('/health')
    @limiter.exempt
    def health_check():
        """Enhanced health check with detailed component status."""
        logger = structlog.get_logger()

        health_status = {
            'status': 'healthy',
            'timestamp': str(datetime.utcnow()),
            'version': '2.0.0',
            'components': {}
        }

        # Database health check
        try:
            db.session.execute(text('SELECT 1'))
            health_status['components']['database'] = {'status': 'healthy', 'latency_ms': 0}
        except Exception as e:
            health_status['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'

        # Cache health check
        try:
            cache.ping()
            health_status['components']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health_status['components']['cache'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'

        # Celery health check
        try:
            inspect = celery.control.inspect()
            stats = inspect.stats()
            if stats:
                health_status['components']['celery'] = {'status': 'healthy', 'workers': len(stats)}
            else:
                health_status['components']['celery'] = {'status': 'unhealthy', 'error': 'No workers available'}
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['components']['celery'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'

        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(ApiResponse.success(health_status).to_dict()), status_code
    
    @app.route('/metrics')
    @limiter.exempt
    def metrics():
        from prometheus_client import generate_latest
        return generate_latest()
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle all HTTP exceptions with consistent response format."""
        logger = structlog.get_logger()
        logger.warning("HTTP exception occurred",
                      status_code=e.code,
                      description=e.description,
                      endpoint=request.endpoint)

        error_response = ErrorResponse(
            error=e.name,
            message=e.description,
            status_code=e.code
        )
        return jsonify(error_response.to_dict()), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle unexpected exceptions with detailed logging."""
        logger = structlog.get_logger()
        logger.error("Unexpected error occurred",
                    error=str(e),
                    error_type=type(e).__name__,
                    endpoint=request.endpoint,
                    method=request.method)

        # Don't expose internal error details in production
        if app.config.get('DEBUG', False):
            message = str(e)
        else:
            message = "An unexpected error occurred"

        error_response = ErrorResponse.internal_error(message)
        return jsonify(error_response.to_dict()), 500

    @app.errorhandler(429)
    def rate_limit_handler(e):
        """Handle rate limiting with enhanced response."""
        logger = structlog.get_logger()
        logger.warning("Rate limit exceeded",
                      client_ip=request.remote_addr,
                      endpoint=request.endpoint)

        retry_after = getattr(e, 'retry_after', None)
        error_response = ErrorResponse.rate_limit_exceeded(retry_after)
        return jsonify(error_response.to_dict()), 429
    
    return app

def make_celery(app):
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Create Flask app
app = create_app()

# Configure Celery with app context
app.app_context().push()
celery = make_celery(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=app.config.get('DEBUG', False))