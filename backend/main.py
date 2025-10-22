from app import app, celery

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=app.config.get('DEBUG', False))