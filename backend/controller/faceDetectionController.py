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
    def __init__(self, images_dir='static/uploads/images/', faces_dir='static/uploads/images/faces',
                 processed_data_file='processed_data.json'):
        self.images_dir = images_dir
        self.faces_dir = faces_dir
        self.processed_data_file = processed_data_file
        self.chroma_client = PersistentClient("./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="face_collection",
                                                                      metadata={"hnsw:space": "cosine"})

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

    def extract_face_embedding(self, face_path: str) -> np.ndarray:
        try:
            embedding = DeepFace.represent(face_path, model_name="Facenet512", enforce_detection=False)[0]['embedding']
            return np.array(embedding)
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None

    def load_processed_data(self) -> Tuple[List[str], List[str], dict]:
        if os.path.exists(self.processed_data_file):
            print('Loading data')
            with open(self.processed_data_file, 'r') as f:
                data = json.load(f)
            return data.get('face_images', []), data.get('all_images', []), data.get('face_to_original_image_map', {})
        return [], [], {}

    def save_processed_data(self, face_images: List[str], all_images: List[str], face_to_original_image_map: dict):
        with open(self.processed_data_file, 'w') as f:
            json.dump({
                'face_images': face_images,
                'all_images': all_images,
                'face_to_original_image_map': face_to_original_image_map
            }, f)

    def quick_load_faces(self) -> List[str]:
        face_images, _, _ = self.load_processed_data()
        return face_images

    def process_faces(self) -> Tuple[List[str], List[str]]:
        face_images, all_images, face_to_original_image_map = self.load_processed_data()
        new_faces = []

        # Process only new images
        for filename in os.listdir(self.images_dir):
            image_path = os.path.join(self.images_dir, filename)
            if filename.lower().endswith(('png', 'jpg', 'jpeg')) and image_path not in all_images:
                print(f"Processing new image: {filename}")
                try:
                    image = cv2.imread(image_path)
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    boxes = self.detect_faces(image_rgb)
                    if boxes is not None and len(boxes) > 0:
                        for i, box in enumerate(boxes):
                            x1, y1, x2, y2 = map(int, box)

                            # Expand the bounding box
                            height, width = image.shape[:2]
                            expand_ratio = 0.3
                            new_x1 = max(0, int(x1 - (x2 - x1) * expand_ratio))
                            new_y1 = max(0, int(y1 - (y2 - y1) * expand_ratio))
                            new_x2 = min(width, int(x2 + (x2 - x1) * expand_ratio))
                            new_y2 = min(height, int(y2 + (y2 - y1) * expand_ratio * 1.5))

                            face = image[new_y1:new_y2, new_x1:new_x2]

                            face_filename = f'detected_face_{len(face_images) + len(new_faces) + 1}.jpg'
                            face_path = os.path.join(self.faces_dir, face_filename)
                            cv2.imwrite(face_path, face)
                            print(f"Saved new face at {face_path}")

                            new_faces.append(face_path)
                            face_to_original_image_map[face_path] = [image_path]
                    else:
                        print("No faces detected in new image.")
                    all_images.append(image_path)
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")

        # Process only new faces for duplicates
        unique_new_faces = []
        for new_face in new_faces:
            is_unique = True
            for existing_face in face_images:
                try:
                    verification = DeepFace.verify(img1_path=new_face, img2_path=existing_face,
                                                   enforce_detection=False)
                    if verification['verified']:
                        is_unique = False
                        face_to_original_image_map[existing_face].extend(face_to_original_image_map[new_face])
                        os.remove(new_face)
                        break
                except Exception as ve:
                    print(f"Error during verification of {new_face} and {existing_face}: {str(ve)}")

            if is_unique:
                unique_new_faces.append(new_face)

        # Update ChromaDB with unique new faces
        for face_path in unique_new_faces:
            embedding = self.extract_face_embedding(face_path)
            if embedding is not None:
                original_images = face_to_original_image_map[face_path]
                self.collection.upsert(
                    documents=original_images,
                    embeddings=[embedding.tolist()],
                    metadatas=[{"face_id": str(len(face_images) + unique_new_faces.index(face_path)),
                                "face_image": face_path}],
                    ids=[f"face_{len(face_images) + unique_new_faces.index(face_path)}"]
                )

        # Update face_images list and save processed data
        face_images.extend(unique_new_faces)
        self.save_processed_data(face_images, all_images, face_to_original_image_map)

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

