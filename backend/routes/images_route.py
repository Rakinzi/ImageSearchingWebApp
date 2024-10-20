# Import necessary libraries and modules
from flask import Blueprint, request, jsonify, render_template
from tasks.image_processing_async import process_images  # Importing async image processing task
import json

import os
from joblib import Parallel, delayed

# Create a Blueprint for images-related routes
images_blueprint = Blueprint('images', __name__)


def process_image(file_data, image_details):
    from controller.image_processing_controller import ImageProcessor
    processor = ImageProcessor(file_data=file_data, image_details=image_details)
    processor.process_images()
    return processor.image_details


# Route for rendering the home page
@images_blueprint.route('/')
def index():
    # Render the 'index.html' template for the home page
    return render_template('index.html')


@images_blueprint.route('/quickly')
def quickly():
    # Render the 'quickly.html' template
    return render_template('quickly.html')


@images_blueprint.route('/serve_images', methods=['POST'])
def serve_images():
    if request.method == 'POST':
        # Get the list of uploaded files from the request
        files = list(request.files.values())
        image_details_list = json.loads(request.form.get('image_details'))

        thumbnails_dir = 'static/uploads/thumbnails'
        if not os.path.exists(thumbnails_dir):
            os.makedirs(thumbnails_dir)
        # Print the number of files received for debugging
        print(len(files))

        file_data = [file.read() for file in files]
        params = list(zip(file_data, image_details_list))

        results = Parallel(n_jobs=-1)(delayed(process_image)(*args) for args in params)
        return jsonify({'status': True, 'message': "Tasks submitted", "results": results}), 202

    # If request method is not POST, return an error response
    return jsonify({'status': False, 'message': 'Invalid Request', }), 400


@images_blueprint.route('/search_images', methods=['POST'])
def search_for_images():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()
        # Initialize the ImageProcessor with the data
        from controller.image_processing_controller import ImageProcessor
        search_processor = ImageProcessor(data=data)

        # Perform the image search and get the results
        message, images, status = search_processor.search_images()
        http_status_code = 200 if status == 1 else 400
        http_status = True if status == 1 else False
        return jsonify({'images': images, "status": http_status, "message": message}), http_status_code
    return jsonify({'status': False, 'message': 'Invalid request method'}), 400


@images_blueprint.route('/get_images', methods=['GET'])
def get_images():
    if request.method == 'GET':
        from controller.image_processing_controller import ImageProcessor
        message, images, status = ImageProcessor().get_inserted_images()
        http_status = True if status == 1 else False
        http_status_code = 200 if status == 1 else 400
        return jsonify({'images': images, "status": http_status, 'message': message}), http_status_code
