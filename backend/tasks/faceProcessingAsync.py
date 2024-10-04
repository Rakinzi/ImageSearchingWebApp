from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
import atexit
from controller.faceDetectionController import FaceProcessor

face_processor = FaceProcessor()


def faces_scheduler():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    executors = {
        'default': ThreadPoolExecutor(1)
    }

    scheduler = BackgroundScheduler(executors=executors)

    def background_task():
        logger.info('Background Task is executing')
        face_processor.process_faces()
        logger.info('Processing Tasks')
        print('Processing those faces brother')

    scheduler.add_job(
        func=background_task,
        trigger='interval',
        minutes=5,
        id='background_task',
        max_instances=1,
        replace_existing=True
    )

    scheduler.start()

    logger.info('Scheduler started!')

    atexit.register(lambda: scheduler.shutdown())
