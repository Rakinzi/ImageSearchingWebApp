# Import necessary modules and classes
from controller.faceDetectionController import FaceProcessor  # FaceProcessor handles face detection-related operations
from flask import Blueprint, request, jsonify, send_file  # Import Flask modules for routing and sending responses

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

# Route to get related images based on a face ID
@faces_blueprint.route('/related_images/<face_id>')
def get_related_images(face_id):
    # Call the get_related_images method to retrieve images related to the given face ID
    related_images, face_image = face_processor.get_related_images(face_id)
    
    # Return a JSON response containing related images and the specific face image
    return jsonify({"related_images": related_images, "face_image": face_image})

# Route to serve an image file given its path
@faces_blueprint.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)

@faces_blueprint.route('/get_faces', methods=['GET'])
def get_faces():
    face_images, all_images, _ = FaceProcessor.load_processed_data()

    return jsonify({
        "face_images": face_images,  # Detected face images
        "all_images": all_images  # All images processed
    })


