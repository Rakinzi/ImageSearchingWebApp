import os
import cv2
import face_recognition
import numpy as np
from flask import Flask, render_template, jsonify, send_file
from chromadb import PersistentClient

app = Flask(__name__)

# Initialize ChromaDB
chroma_client = PersistentClient("./chroma_db")
collection = chroma_client.get_or_create_collection(name="face_collection", metadata={"hnsw:space": "cosine"})

# Directory containing images
IMAGE_DIR = "./static/uploads/images"
FACES_DIR = "./static/uploads/images/faces"

# Ensure the faces directory exists
os.makedirs(FACES_DIR, exist_ok=True)

def process_images():
    known_face_encodings = []
    known_face_images = []
    all_image_paths = []
    face_images = []

    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(IMAGE_DIR, filename)
            print(filename)
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                if not known_face_encodings or not any(
                        face_recognition.compare_faces(known_face_encodings, face_encoding)):
                    known_face_encodings.append(face_encoding)
                    known_face_images.append(image_path)

                    # Extract and save the face image
                    top, right, bottom, left = face_location
                    face_image = image[top:bottom, left:right]
                    face_image = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
                    face_filename = f"face_{len(face_images)}.jpg"
                    face_path = os.path.join(FACES_DIR, face_filename)
                    cv2.imwrite(face_path, face_image)
                    face_images.append(face_path)

            all_image_paths.append(image_path)

    # Store face encodings and image paths in ChromaDB
    for i, (encoding, image_path) in enumerate(zip(known_face_encodings, known_face_images)):
        collection.add(
            documents=[image_path],
            embeddings=[encoding.tolist()],
            metadatas=[{"face_id": str(i), "face_image": face_images[i]}],
            ids=[f"face_{i}"]
        )

    return face_images, all_image_paths

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process')
def process():
    face_images, all_images = process_images()
    print(f'Faces : {face_images}')
    print(f"All Images: {all_images}")
    return jsonify({
        "face_images": face_images,
        "all_images": all_images
    })

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)

@app.route('/related_images/<face_id>')
def get_related_images(face_id):
    results = collection.query(
        query_embeddings=[collection.get(ids=[f"face_{face_id}"], include=['embeddings'])['embeddings'][0]],
        n_results=10,
        include=['documents', 'metadatas']
    )
    related_images = results["documents"][0]
    face_image = results["metadatas"][0][0]
    print(face_image)
    return jsonify({"related_images": related_images, "face_image": face_image})

if __name__ == '__main__':
    app.run(debug=True)