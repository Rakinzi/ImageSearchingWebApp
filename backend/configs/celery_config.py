from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['broker_url'])
    celery.conf.update(app.config)
    celery.autodiscover_tasks(['tasks'])
    return celery
