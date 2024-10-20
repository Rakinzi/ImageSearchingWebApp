# Import necessary modules and classes
from controller.face_detection_controller import FaceProcessor  # FaceProcessor handles face detection-related operations
from flask import Blueprint, request, jsonify, send_file  # Import Flask modules for routing and sending responses
import os

# Initialize an instance of FaceProcessor to handle face detection
face_processor = FaceProcessor()

# Create a Blueprint for handling face detection-related routes
faces_blueprint = Blueprint('faces', __name__)


# Route to process faces and return detected face images and all images
@faces_blueprint.route('/process')
def process():
    # Call the process_faces method to detect faces in images
    face_images, all_images = face_processor.process_faces()

    # Return a JSON response containing the detected face images and all images
    return jsonify({
        "face_images": face_images,  # Detected face images
        "all_images": all_images  # All images processed
    })


# Route to get rela ted images based on a face ID
@faces_blueprint.route('/related_images/<face_id>')
def get_related_images(face_id):
    # Call the get_related_images method to retrieve images related to the given face ID
    faces_dir = 'static/uploads/faces'
    related_images, face_image = face_processor.get_related_images(face_id)
    face_filename = f'{face_id}.jpg'
    face_path = os.path.join(faces_dir, face_filename)
    print(face_path)
    # Return a JSON response containing related images and the specific face image
    return jsonify({"related_images": related_images, "face_image": face_path})


# Route to serve an image file given its path
@faces_blueprint.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)


@faces_blueprint.route('/get_faces', methods=['GET'])
def get_faces():
    face_images, all_images, tester = face_processor.load_data_from_db()
    face_images = [os.path.normpath(image) for image in face_images]
    return jsonify({
        "face_images": face_images,  # Detected face images
        "all_images": all_images,   # All images processed
        'face_to_original_map': tester
    })
