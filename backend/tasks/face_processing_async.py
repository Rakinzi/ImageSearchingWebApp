from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
import atexit



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
        from controller.face_detection_controller import FaceProcessor

        face_processor = FaceProcessor()
        logger.info('Background Task is executing')
        face_processor.process_faces()
        logger.info('Processing Tasks')

    scheduler.add_job(
        func=background_task,
        trigger='interval',
        seconds=10,
        id='background_task',
        max_instances=1,
        replace_existing=False
    )

    scheduler.start()

    logger.info('Scheduler started!')

    atexit.register(lambda: scheduler.shutdown())
