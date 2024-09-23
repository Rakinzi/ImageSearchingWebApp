import os
from controller.faceDetectionController import FaceDetector
from flask import Blueprint, request, jsonify, render_template, send_file

faces_blueprint = Blueprint('faces', __name__)

face_detector = FaceDetector()


@faces_blueprint.route('/')
def index():
    return render_template('index.html')


@faces_blueprint.route('/process')
def process():
    face_images, all_images = face_detector.process_images()
    print(f'Faces : {face_images}')
    print(f"All Images: {all_images}")
    return jsonify({
        "face_images": face_images,
        "all_images": all_images
    })


@faces_blueprint.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)


@faces_blueprint.route('/related_images/<face_id>')
def get_related_images(face_id):
    related_images, face_image = face_detector.get_related_images(face_id)
    return jsonify({"related_images": related_images, "face_image": face_image})
