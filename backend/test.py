import os
import torch
from flask import Flask, render_template, jsonify, send_file
from chromadb import PersistentClient
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
from torchvision import transforms
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Initialize ChromaDB
chroma_client = PersistentClient("./chroma_db")
collection = chroma_client.get_or_create_collection(name="face_collection", metadata={"hnsw:space": "cosine"})

# Directory containing images
IMAGE_DIR = "./static/uploads/images"
FACES_DIR = "./static/uploads/images/faces"

# Ensure the faces directory exists
os.makedirs(FACES_DIR, exist_ok=True)

# Initialize MTCNN and InceptionResnetV1
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

# Image transformation
transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])


def detect_faces(img):
    # Convert image to tensor and use MTCNN to detect faces
    boxes, probs = mtcnn.detect(img)

    # Filter out low-confidence detections
    if boxes is not None:
        boxes = [box for box, prob in zip(boxes, probs) if prob > 0.98]
        print(probs)
    print(f"Detected {len(boxes) if boxes is not None else 0} faces for this image")
    return boxes


def is_new_face(embedding, known_face_embeddings, similarity_threshold=0.7):
    if not known_face_embeddings:
        return True
    similarities = cosine_similarity([embedding], known_face_embeddings)[0]
    return not any(sim > similarity_threshold for sim in similarities)


def process_images():
    known_face_embeddings = []
    known_face_images = []
    all_image_paths = []
    face_images = []

    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(IMAGE_DIR, filename)
            print(f"Processing {filename}")

            try:
                # Load image
                img = Image.open(image_path)

                # Detect faces
                boxes = detect_faces(img)

                # Check if there are any detected faces
                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        # Extract face
                        x1, y1, x2, y2 = [int(x) for x in box]
                        face = img.crop((x1, y1, x2, y2))
                        face_tensor = transform(face).unsqueeze(0).to(device)

                        # Get embedding
                        with torch.no_grad():
                            embedding = resnet(face_tensor).cpu().numpy().flatten()

                        # Check if it's a new face
                        if is_new_face(embedding, known_face_embeddings):
                            known_face_embeddings.append(embedding)
                            known_face_images.append(image_path)

                            # Save face image
                            face_filename = f"face_{len(face_images)}.jpg"
                            face_path = os.path.join(FACES_DIR, face_filename)
                            face.save(face_path)
                            face_images.append(face_path)
                            print(f"New face detected and saved: {face_filename}")
                        else:
                            print(f"Duplicate face detected in {filename}")
                else:
                    print(f"No faces detected in {filename}")

                all_image_paths.append(image_path)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    # Store face embeddings and image paths in ChromaDB
    for i, (embedding, image_path) in enumerate(zip(known_face_embeddings, known_face_images)):
        collection.add(
            documents=[image_path],
            embeddings=embedding.tolist(),
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
    return jsonify({
        "face_images": face_images,
        "all_images": all_images
    })


@app.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)


@app.route('/related_images/<face_id>')
def get_related_images(face_id):
    # Query the collection for related images
    results = collection.query(
        query_embeddings=[collection.get(ids=[f"face_{face_id}"], include=['embeddings'])['embeddings'][0]],
        n_results=10,
        include=['documents', 'metadatas']
    )
    related_images = results["documents"][0]
    face_image = results["metadatas"][0][0]["face_image"]
    return jsonify({"related_images": related_images, "face_image": face_image})


if __name__ == '__main__':
    app.run(debug=True)
