# Import necessary libraries and modules
from flask import Blueprint, request, jsonify, render_template
from tasks.imageProcessingAsync import process_images  # Importing async image processing task
import json
from controller.imageProcessingController import ImageProcessor  # Image processor for handling search

# Create a Blueprint for images-related routes
images_blueprint = Blueprint('images', __name__)

# Route for rendering the home page
@images_blueprint.route('/')
def index():
    # Render the 'index.html' template for the home page
    return render_template('index.html')

# Route for rendering a different page (e.g., quickly.html)
@images_blueprint.route('/quickly')
def quickly():
    # Render the 'quickly.html' template
    return render_template('quickly.html')

# Route for handling image upload and processing
@images_blueprint.route('/serve_images', methods=['POST'])
def serve_images():
    if request.method == 'POST':
        # Get the list of uploaded files from the request
        files = list(request.files.values())
        # Get image details (metadata) from the form, and parse the JSON
        print(request.form.get('image_details'))
        image_details_list = json.loads(request.form.get('image_details'))
        
        # Print the number of files received for debugging
        print(len(files))
        
        # List to store task IDs for asynchronous processing
        task_ids = []
        
        # Iterate over files and corresponding image details
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

@images_blueprint.route('/get_images', methods=['GET'])
def get_images():
    if request.method == 'GET':
        message, images, status = ImageProcessor().get_inserted_images()
        http_status = True if status == 1 else False
        http_status_code = 200 if status == 1 else 400
        return jsonify({'images': images, "status": http_status, 'message': message}), http_status_code


# Route for handling image search functionality
@images_blueprint.route('/search_images', methods=['POST'])
def search_for_images():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()
        # Initialize the ImageProcessor with the data
        search_processor = ImageProcessor(data=data)
        
        # Perform the image search and get the results
        message, images, status = search_processor.search_images()
        
        # Determine the HTTP status based on the success of the operation
        http_status = 200 if status == 1 else 400
        
        # Return a JSON response with the search results
        return jsonify({'images': images, "status": status == 1, "message": message}), http_status
    
    # If request method is not POST, return an error response
    return jsonify({'status': False, 'message': 'Invalid request method'}), 400
