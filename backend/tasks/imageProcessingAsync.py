from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_images(file_data, image_details):
    try:
        logger.info("Starting to process image with details: %s", image_details)
        print("Emmmmm")
        # Additional logging to verify data
        logger.info("Received file data of length: %d", len(file_data))

        from controller.imageProcessingController import ImageProcessor
        image_processor = ImageProcessor(file_data=file_data, image_details=image_details)

        # Log before processing
        logger.info("Processing image now...")
        result = image_processor.process_images()
        print(result)

        # Log after processing
        logger.info("Finished processing image with result: %s", result)
        return result
    except Exception as e:
        logger.error("Error processing image: %s", str(e))
        return {'status': False, 'error': str(e)}


# @shared_task
# def process_faces():

