import json
import os
from typing import List, Tuple
import cv2
import numpy as np
import torch
from deepface import DeepFace
from facenet_pytorch import MTCNN
from sklearn.metrics.pairwise import cosine_similarity
from chromadb import PersistentClient

class FaceProcessor:
    def __init__(self, images_dir='static/uploads/images/', faces_dir='static/uploads/images/faces', processed_data_file='processed_data.json'):
        self.images_dir = images_dir
        self.faces_dir = faces_dir
        self.processed_data_file = processed_data_file
        self.chroma_client = PersistentClient("./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="face_collection", metadata={"hnsw:space": "cosine"})

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.faces_dir, exist_ok=True)

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

    def detect_faces(self, image_rgb):
        boxes, probs = self.mtcnn.detect(image_rgb)
        if boxes is not None:
            boxes = [box for box, prob in zip(boxes, probs) if prob > 0.99]
        print(f"Detected {len(boxes) if boxes is not None else 0} faces for this image")
        return boxes

    def is_new_face(self, embedding: np.ndarray, known_face_embeddings: List[np.ndarray], similarity_threshold: float = 0.7) -> bool:
        if not known_face_embeddings:
            return True
        similarities = cosine_similarity([embedding], known_face_embeddings)[0]
        return not any(sim > similarity_threshold for sim in similarities)

    def extract_face_embedding(self, face_path: str) -> np.ndarray:
        try:
            embedding = DeepFace.represent(face_path, model_name="Facenet512", enforce_detection=False)[0]['embedding']
            return np.array(embedding)
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None

    def load_processed_data(self) -> Tuple[List[str], List[str]]:
        if os.path.exists(self.processed_data_file):
            print('Loading data')
            with open(self.processed_data_file, 'r') as f:
                data = json.load(f)
            return data.get('face_images', []), data.get('all_images', [])
        return [], []

    def save_processed_data(self, face_images: List[str], all_images: List[str]):
        with open(self.processed_data_file, 'w') as f:
            json.dump({'face_images': face_images, 'all_images': all_images}, f)

    def process_faces(self) -> Tuple[List[str], List[str]]:
        face_images, all_images = self.load_processed_data()
        known_face_embeddings = []

        for face_path in face_images:
            embedding = self.extract_face_embedding(face_path)
            if embedding is not None:
                known_face_embeddings.append(embedding)

        new_images = [img for img in os.listdir(self.images_dir) if
                      img.lower().endswith(('png', 'jpg', 'jpeg')) and os.path.join(self.images_dir,
                                                                                    img) not in all_images]

        for filename in new_images:
            image_path = os.path.join(self.images_dir, filename)
            print(f"Processing {filename}")

            try:
                image = cv2.imread(image_path)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                boxes = self.detect_faces(image_rgb)
                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = map(int, box)

                        # Expand the bounding box
                        height, width = image.shape[:2]
                        expand_ratio = 0.3  # Increase this value to expand the area more

                        new_x1 = max(0, int(x1 - (x2 - x1) * expand_ratio))
                        new_y1 = max(0, int(y1 - (y2 - y1) * expand_ratio))
                        new_x2 = min(width, int(x2 + (x2 - x1) * expand_ratio))
                        new_y2 = min(height,
                                     int(y2 + (y2 - y1) * expand_ratio * 1.5))  # Expand more vertically for neck

                        face = image[new_y1:new_y2, new_x1:new_x2]

                        face_filename = f'detected_face_{len(face_images) + 1}.jpg'
                        face_path = os.path.join(self.faces_dir, face_filename)
                        cv2.imwrite(face_path, face)
                        print(f"Saved face at {face_path}")

                        embedding = self.extract_face_embedding(face_path)
                        if embedding is not None:
                            if self.is_new_face(embedding, known_face_embeddings):
                                known_face_embeddings.append(embedding)
                                face_images.append(face_path)
                                print(f"New face detected and saved {face_path}")

                                self.collection.add(
                                    documents=[image_path],
                                    embeddings=[embedding.tolist()],
                                    metadatas=[{"face_id": str(len(face_images) - 1), "face_image": face_path}],
                                    ids=[f"face_{len(face_images) - 1}"]
                                )
                            else:
                                print(f"Duplicate face detected in {filename}")
                                os.remove(face_path)
                        else:
                            print(f"Failed to extract embedding for face in {filename}")
                            os.remove(face_path)
                else:
                    print("No faces detected.")
                all_images.append(image_path)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

        self.save_processed_data(face_images, all_images)
        return face_images, all_images
    def get_related_images(self, face_id: str) -> Tuple[List[str], str]:
        results = self.collection.query(
            query_embeddings=[self.collection.get(ids=[f"face_{face_id}"], include=['embeddings'])['embeddings'][0]],
            n_results=10,
            include=['documents', 'metadatas']
        )
        related_images = results["documents"][0]
        face_image = results["metadatas"][0][0]["face_image"]
        return related_images, face_image
