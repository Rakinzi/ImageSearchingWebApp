import os
from typing import List, Tuple, Dict, Set
import cv2
import numpy as np
import torch
from deepface import DeepFace
from facenet_pytorch import MTCNN
import sqlite3
from joblib import Parallel, delayed
from chromadb import PersistentClient
import random
import time
import uuid

def generate_filename():
    return f"{uuid.uuid4()}_{int(time.time())}.jpg"

def process_single_image(image_path: str, faces_dir: str, mtcnn, device) -> Tuple[List[str], List[str], Dict[str, List[str]]]:
    if not image_path.lower().endswith(('png', 'jpg', 'jpeg')):
        return [], [], {}

    print(f"Processing new image: {os.path.basename(image_path)}")
    try:
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        boxes, probs = mtcnn.detect(image_rgb)
        new_faces = []
        if boxes is not None:
            boxes = [box for box, prob in zip(boxes, probs) if prob > 0.99]
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

                face_filename = generate_filename()
                face_path = os.path.join(faces_dir, face_filename)

                cv2.imwrite(face_path, face)
                print(f"Saved new face at {face_path}")

                new_faces.append(face_path)

        return new_faces, [image_path], {face: [image_path] for face in new_faces}
    except Exception as e:
        print(f"Error processing {os.path.basename(image_path)}: {str(e)}")
        return [], [], {}

class FaceProcessor:
    def __init__(self, images_dir='static/uploads/images/', faces_dir='static/uploads/faces'):
        self.images_dir = images_dir
        self.faces_dir = faces_dir

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.faces_dir, exist_ok=True)

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

        self.chroma_client = PersistentClient("./chroma_db")
        self.face_collection = self.chroma_client.get_or_create_collection("face_embeddings",
                                                                           metadata={"hnsw:space": "cosine"})
        self.create_faces_table()

    def create_faces_table(self):
        with sqlite3.connect("faces_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id TEXT UNIQUE,
                    images_linked TEXT,
                    image_tagging TEXT DEFAULT NULL
                )
            ''')
            conn.commit()

    def insert_face_data(self, image_id: str, images_linked: str):
        with sqlite3.connect("faces_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO faces (image_id, images_linked)
                VALUES (?, ?)
            ''', (image_id, images_linked))
            conn.commit()

    def detect_faces(self, image_rgb):
        boxes, probs = self.mtcnn.detect(image_rgb)
        if boxes is not None:
            boxes = [box for box, prob in zip(boxes, probs) if prob > 0.99]
        print(f"Detected {len(boxes) if boxes is not None else 0} faces for this image")
        return boxes

    def extract_face_embedding(self, face_path: str) -> np.ndarray:
        try:
            embedding = DeepFace.represent(face_path, model_name="Facenet512", enforce_detection=False, detector_backend='dlib')[0]['embedding']
            return np.array(embedding)
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None

    def load_data_from_db(self) -> Tuple[List[str], List[str], dict]:
        with sqlite3.connect("faces_database.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            sql = "SELECT image_id, images_linked from faces"
            cursor.execute(sql)
            rows = cursor.fetchall()

            face_images = []
            all_images = set()
            face_to_original_map = {}

            for row in rows:
                face_images.append(row['image_id'])
                split_images = row['images_linked'].split(',')
                for split_image in split_images:
                    all_images.add(split_image.strip())
                face_to_original_map[row['image_id']] = list(set(split_images))

            all_images = list(all_images)
            face_images = list(set(face_images))

            return face_images, all_images, face_to_original_map


    def delete_and_restructure_faces(self):
        with sqlite3.connect("faces_database.db") as conn:
            cursor = conn.cursor()
            query = "DELETE FROM faces"
            cursor.execute(query)
            conn.commit()

    def get_file_paths(self):
        return [os.path.join(self.images_dir, file) for file in os.listdir(self.images_dir)]


    def add_faces_to_chromadb(self, face_images: List[str]) -> Dict[str, np.ndarray]:
        face_embeddings = {}
        for face in face_images:
            embedding = self.extract_face_embedding(face)
            if embedding is not None:
                face_embeddings[face] = embedding
                self.face_collection.upsert(
                    documents=[face],
                    embeddings=[embedding.tolist()],
                    ids=[face]
                )
        return face_embeddings

    def compare_faces(self, face_images: List[str], face_to_original_image_map: Dict[str, List[str]]) -> Tuple[
        List[str], Set[str], Dict[str, List[str]]]:
        faces_to_remove = set()

        for face in face_images:
            if face in faces_to_remove:
                continue

            results = self.face_collection.query(
                query_embeddings=[self.face_collection.get(ids=[face], include=['embeddings'])['embeddings'][0]],
                n_results=len(face_images)
            )

            print(f" Results for {face} are: ",results)
            for i, (similar_face, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                if i == 0 or similar_face == face:  # Skip the first result (self) and any exact matches
                    continue

                if similar_face in faces_to_remove:
                    continue

                print(f"Comparing {face} with {similar_face}, distance: {distance}")

                if distance < 0.55:  # Using 0.4 as the threshold
                    print(f"Duplicate found, marking for removal: {similar_face}")
                    face_to_original_image_map[face].extend(face_to_original_image_map[similar_face])
                    face_to_original_image_map[face] = list(set(face_to_original_image_map[face]))
                    print(f"For face {face} these are the linked images {face_to_original_image_map[face]}")
                    faces_to_remove.add(similar_face)


        return face_images, faces_to_remove, face_to_original_image_map

    def process_faces(self) -> Tuple[List[str], List[str]]:
        face_images, all_images, face_to_original_image_map = self.load_data_from_db()

        print(f"{len(face_images)} Face images before processing:", face_images)

        # Get all image paths
        image_paths = self.get_file_paths()
        print('All Images ', all_images)
        print('Face Images ', image_paths)

        if set(all_images) == set(image_paths):
            print('Matched')
            return face_images, all_images

        # Process images in parallel
        results = Parallel(n_jobs=-1)(
            delayed(process_single_image)(
                image_path, self.faces_dir, self.mtcnn, self.device
            ) for image_path in image_paths if image_path not in all_images
        )

        # Combine results
        for new_faces, new_all_images, new_face_map in results:
            face_images.extend(new_faces)
            all_images.extend(new_all_images)
            for face, original_images in new_face_map.items():
                if face in face_to_original_image_map:
                    face_to_original_image_map[face].extend(original_images)
                else:
                    face_to_original_image_map[face] = original_images

        # Remove duplicates
        face_images = list(set(face_images))
        all_images = list(set(all_images))

        # Add all face embeddings to ChromaDB
        face_embeddings = self.add_faces_to_chromadb(face_images)

        # Compare faces using ChromaDB
        face_images, faces_to_remove, face_to_original_image_map = self.compare_faces(face_images,
                                                                                       face_to_original_image_map)

        print(f"Not unique", face_images)
        face_images = [face for face in face_images if face not in faces_to_remove]
        print(f"Unique faces", face_images)
        # Update face_images list
        face_images = [face for face in face_images if os.path.exists(face)]

        face_images = list(set(face_images))

        print("Remaining faces after processing:")
        for face in face_images:
            print(f"- {face}")

        # Update SQLite with unique faces
        self.delete_and_restructure_faces()
        for face_path in face_images:
            if os.path.exists(face_path):
                original_images = [image.replace(" ", "") for image in face_to_original_image_map[face_path]]
                images_linked = ','.join(original_images)
                self.insert_face_data(face_path, images_linked)
                print(f"Inserted {face_path}, images linked are {images_linked}")
            else:
                print(f"File not found for {face_path}, skipping database insertion and processing.")

        # Remove faces marked for deletion from ChromaDB
        self.face_collection.delete(ids=list(faces_to_remove))

        # Actually remove the files marked for deletion
        for face in faces_to_remove:
            if os.path.exists(face):
                os.remove(face)

        return face_images, all_images

    def get_related_images(self, face_id: str) -> Tuple[List[str], str]:
        with sqlite3.connect("faces_database.db") as conn:
            cursor = conn.cursor()
            face_filename = f'{face_id}.jpg'
            face_path = os.path.join(self.faces_dir, face_filename)
            print(face_path)
            cursor.execute('SELECT images_linked FROM faces WHERE image_id = ?', (face_path,))
            result = cursor.fetchone()
            if result:
                images_linked = result[0].split(',')
                print(images_linked)
                return images_linked, face_id
            return [], face_id