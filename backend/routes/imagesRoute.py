from flask import Blueprint, request, jsonify
from tasks.imageProcessingAsync import process_images
import json
from controller.imageProcessingController import ImageProcessor

images_blueprint = Blueprint('images', __name__)


@images_blueprint.route('/')
def index():
    return 'Hello Photoooooooo'


@images_blueprint.route('/serve_images', methods=['POST'])
def serve_images():
    if request.method == 'POST':
        files = list(request.files.values())
        image_details_list = json.loads(request.form.get('image_details'))
        print(len(files))
        task_ids = []
        for file, image_details in zip(files, image_details_list):
            file_data = file.read()
            image_details['filename'] = file.filename
            task = process_images.apply_async(args=(file_data, image_details))
            print(task)
            print(file.filename)
            task_ids.append(task.id)

        print(task_ids)
        return jsonify({'status': True, 'message': "Tasks submitted", 'task_ids': task_ids}), 202
    return jsonify({'status': False, 'message': 'Invalid Request'}), 400


@images_blueprint.route('/search_images', methods=['POST'])
def search_for_images():
    if request.method == "POST":
        data = request.get_json()
        search_processor = ImageProcessor(data=data)
        message, images, status = search_processor.search_images()
        http_status = 200 if status == 1 else 400
        return jsonify({'images': images, "status": status == 1, "message": message}), http_status
    return jsonify({'status': False, 'message': 'Invalid request method'}), 400
