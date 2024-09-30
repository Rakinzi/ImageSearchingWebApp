# Import necessary libraries and modules
from flask import Blueprint, request, jsonify, render_template
from tasks.imageProcessingAsync import process_images  # Importing async image processing task
import json
from controller.imageProcessingController import ImageProcessor
import exifread
from PIL import Image
from io import BytesIO
import os

# Create a Blueprint for images-related routes
images_blueprint = Blueprint('images', __name__)

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
        # Get image details (metadata) from the form, and parse the JSON
        print(request.form.get('image_details'))
        image_details_list = json.loads(request.form.get('image_details'))

        thumbnails_dir = 'static/uploads/thumbnails'
        if not os.path.exists(thumbnails_dir):
            os.makedirs(thumbnails_dir)
        # Print the number of files received for debugging
        print(len(files))
        
        # List to store task IDs for asynchronous processing
        task_ids = []

        for file, image_details in zip(files, image_details_list):
            # Read file content (image data)
            file_data = file.read()
            # Add filename to image details
            image_details['filename'] = file.filename
            # Submit the file for async processing and store the task ID
            task = process_images.apply_async(args=(file_data, image_details))
            
            # Print task and filename for debugging
            print(task)
            print(file.filename)
            
            # Append task ID to the list
            task_ids.append(task.id)

        # Print all task IDs for debugging purposes
        print(task_ids)
        
        # Return a JSON response indicating success, along with task IDs
        return jsonify({'status': True, 'message': "Tasks submitted", 'task_ids': task_ids}), 202
    
    # If request method is not POST, return an error response
    return jsonify({'status': False, 'message': 'Invalid Request'}), 400


# @images_blueprint.route('/upload', methods=['POST'])
# def upload_images():
#     if request.method == 'POST':
#
#         files = list(request.files.values())  # Get the uploaded files
#         image_details_list = []  # Initialize a new list for image details
#
#
#         for file in files:
#             file_data = file.read()
#             image_details = {}  # Create a new dict for each image's details
#             image_details['filename'] = file.filename  # Add the filename to the details
#
#             # Step 1: Extract metadata using exifread
#             file_data_io = BytesIO(file_data)  # Convert bytes to a file-like object
#             exif_data = exifread.process_file(file_data_io, details=False)  # Extract EXIF metadata
#
#             # Debug print to check if exif_data is being populated
#             print(f"EXIF data for {file.filename}: {exif_data}")
#
#             # Step 2: Handle case where EXIF data is not available
#             if exif_data:
#                 exif = {}
#                 latitude = None
#                 longitude = None
#
#                 for tag in crucial_tags:
#                     if tag in exif_data:
#                         exif[tag] = str(exif_data[tag])  # Store the EXIF tag and its value as a string
#                         # Extract GPS coordinates if available
#                         if tag == 'GPS GPSLatitude':
#                             latitude = str(exif_data[tag])
#                         elif tag == 'GPS GPSLongitude':
#                             longitude = str(exif_data[tag])
#
#                 # Step 3: Update image_details with the extracted EXIF metadata
#                 image_details.update(exif)
#
#                 # Step 4: Reverse geocode if both latitude and longitude are available
#                 if latitude and longitude:
#                     try:
#                         location = geolocator.reverse(f"{latitude}, {longitude}")
#                         if location:
#                             image_details['location'] = location.address  # Add location to image details
#                     except Exception as e:
#                         image_details['location'] = f"Error retrieving location: {str(e)}"
#
#             else:
#                 # If EXIF is missing, note that no metadata was found
#                 image_details['metadata'] = 'No EXIF metadata found'
#
#             # Step 5: Generate a thumbnail
#             try:
#                 image = Image.open(BytesIO(file_data))  # Open image from the byte data
#                 image.thumbnail((128, 128))  # Resize image to 128x128 pixels (or your preferred size)
#                 thumbnail_io = BytesIO()
#                 image.save(thumbnail_io, format='JPEG')  # Save the thumbnail as JPEG to a BytesIO object
#                 thumbnail_io.seek(0)
#
#                 thumbnail_path = os.path.join('static/uploads/thumbnails', f"thumb_{file.filename}")
#
#                 # Save the thumbnail to the filesystem
#                 with open(thumbnail_path, 'wb') as f:
#                     f.write(thumbnail_io.read())
#
#                 print("Images saved")
#                 image_details['thumbnail'] = thumbnail_path  # Add thumbnail path to image details
#             except Exception as e:
#                 image_details['thumbnail'] = f"Error generating thumbnail: {str(e)}"
#
#             # Add the processed image details to the list
#             image_details_list.append(image_details)
#
#         print(image_details_list)
#         return jsonify({"image_details": image_details_list}), 200

@images_blueprint.route('/search_images', methods=['POST'])
def search_for_images():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()
        # Initialize the ImageProcessor with the data
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
        message, images, status = ImageProcessor().get_inserted_images()
        http_status = True if status == 1 else False
        http_status_code = 200 if status == 1 else 400
        return jsonify({'images': images, "status": http_status, 'message': message}), http_status_code
