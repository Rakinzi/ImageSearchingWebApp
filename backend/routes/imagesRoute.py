import os.path

from flask import Blueprint, request, jsonify
from controller.searchController import ImageSearcher
import json

images_blueprint = Blueprint('images', __name__)


@images_blueprint.route('/')
def index():
    return 'Hello'


@images_blueprint.route('/serve_images', methods=['POST'])
def serve_images():
    if request.method == 'POST':
        return jsonify({"message": "We cool", "status": True}), 200
    #     files = request.files.values()
    #     image_details_list = json.loads(request.form.get('image_details'))
    #     print(files)
    #     print(image_details_list)
    #     if not files or not image_details_list:
    #         return jsonify({"error": "No images or files have been found"}), 400
    #
    #     uploaded_images = []
    #     images = []
    #     for i, file in enumerate(files):
    #         if file:
    #
    #             image_file = file
    #             image_data = file.read()
    #             image_format = file.content_type.split('/')[1]
    #             image_details = image_details_list[i] if i < len(image_details_list) else {}
    #             image_date = image_details.get('creationDate')
    #
    #             image_path = os.path.join('static/uploads/images', file.filename)
    #             with open(image_path, 'wb') as f:
    #                 f.write(image_data)
    #             print('Image saved')
    #
    #             blob = bucket.blob(f"uploads/{file.filename}")
    #             blob.upload_from_filename(image_path)
    #             image_url = blob.public_url
    #
    #             searcher = ImageSearcher()
    #             processor = searcher.seed_one_image(
    #                 image_uri=image_url, image_format=image_format,
    #                 image_data=image_data, image_date=image_date,
    #             )
    #
    #             if processor != 0:
    #                 images = searcher.get_inserted_images()
    #                 images = images['ids']
    #                 print(images)
    #                 uploaded_images.append({
    #                     'filename': image_file.filename,
    #                     'creationDate': image_date,
    #                     'uri': image_url,
    #                     'saved_path': image_path
    #                 })
    #             else:
    #                 print("Error inserting images")
    #                 return jsonify({'images': None, 'status': False}), 400
    #         else:
    #             return jsonify({'images': None, 'status': False, 'message': "Invalid type mate"}), 400
    #     return jsonify({'images': images, 'status': True, 'message': 'All is well'}), 200
    # else:
    #     return jsonify({'images': None, 'status': False, 'message': 'Invalid Request'}), 400


# @images_blueprint.route('/serve_images', methods=['POST'])
# def serve_images():
#     if request.method == 'POST':
#         if 'image' in request.files and 'image_details' in request.form:
#             try:
#                 image_details = json.loads(request.form.get('image_details'))
#
#                 image_file = request.files['image']
#                 image_data = image_file.read()
#                 mime_type = image_file.content_type
#
#                 image_format = mime_type.split('/')[1]
#                 image_date = image_details['creationDate']
#                 image_url = image_details['uri']
#                 print(image_url)
#
#                 # Initialize ImageSearcher and process the image
#                 searcher = ImageSearcher()
#                 processor = searcher.seed_one_image(
#                     image_uri=image_url, image_format=image_format,
#                     image_data=image_data, image_date=image_date,
#                 )
#                 if processor != 0:
#                     images = searcher.get_inserted_images()
#                     images = images['ids']
#                     print(images)
#                     return jsonify({'images': images, 'status': True}), 200
#                 else:
#                     return jsonify({'images': None, 'status': False}), 400
#             except Exception as e:
#                 print(f"Error: {e}")
#                 return jsonify({'images': None, 'status': False, 'message': 'Failed'}), 400
#         else:
#             print("No file uploaded")
#             print(request.files.keys())
#             return jsonify({'images': None, 'status': False, 'message': 'No File Uploaded'}), 400
#     else:
#         return jsonify({'images': None, 'status': False, 'message': 'Invalid Request'}), 400


@images_blueprint.route('/search_images', methods=['POST'])
def search_for_images():
    data = request.get_json()  # This expects JSON data
    if 'query' in data:
        query = data['query']
        searcher = ImageSearcher()
        images = searcher.search_one_image(query=query)
        if images is None:
            return jsonify({'images': None, 'status': False, 'message': 'No images matches your query'}), 400
        return jsonify({'images': images, 'status': True}), 200
    else:
        return jsonify({'images': None, 'status': False, 'message': 'No images matches your query'}), 400
