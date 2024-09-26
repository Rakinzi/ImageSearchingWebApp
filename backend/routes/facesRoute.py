from controller.faceDetectionController import FaceProcessor
from flask import Blueprint, request, jsonify, send_file

face_processor = FaceProcessor()
faces_blueprint = Blueprint('faces', __name__)

@faces_blueprint.route('/process')
def process():
    face_images, all_images = face_processor.process_faces()
    return jsonify({
        "face_images": face_images,
        "all_images": all_images
    })


@faces_blueprint.route('/related_images/<face_id>')
def get_related_images(face_id):
    related_images, face_image = face_processor.get_related_images(face_id)
    return jsonify({"related_images": related_images, "face_image": face_image})


@faces_blueprint.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)