import json
import os
from typing import List, Tuple
import cv2
import numpy as np
import torch
from deepface import DeepFace
from facenet_pytorch import MTCNN
import sqlite3


class FaceProcessor:
    def __init__(self, images_dir='static/uploads/images/', faces_dir='static/uploads/images/faces',
                 processed_data_file='processed_data.json'):
        self.images_dir = images_dir
        self.faces_dir = faces_dir
        self.processed_data_file = processed_data_file

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.faces_dir, exist_ok=True)

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

        self.create_faces_table()

    def get_db_connection(self):
        """Create a new database connection."""
        return sqlite3.connect("faces_database.db")

    def create_faces_table(self):
        with self.get_db_connection() as conn:
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
        with self.get_db_connection() as conn:
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
        processed_faces = set()  # Initialize as an empty set

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

                            # Extract embedding for the new face
                            embedding = self.extract_face_embedding(face_path)
                            if embedding is not None:
                                new_faces.append(face_path)
                                face_to_original_image_map[face_path] = [image_path]
                            else:
                                print("This is not a face")
                                os.remove(face_path)
                    else:
                        print("No faces detected in new image.")
                    all_images.append(image_path)
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")

        print("New faces detected:", new_faces)
        unique_new_faces = []
        faces_to_remove = set()
        face_images = new_faces if len(face_images) == 0 else face_images

        # Compare new faces against existing faces only
        for new_face in new_faces:
            if new_face in processed_faces:
                print(f"Skipping already processed new face: {new_face}")
                continue

            processed_faces.add(new_face)  # Mark new face as processed
            print(f"Checking new face: {new_face}")
            is_unique = True

            for existing_face in face_images:
                if new_face == existing_face:
                    print(f"Skipping the image is the same {new_face}")
                    continue

                if existing_face in faces_to_remove:
                    print(f"Skipping existing face marked for removal: {existing_face}")
                    continue

                if existing_face in processed_faces:
                    print(f"Skipping this as it has been processed before")
                    continue

                print(f"Comparing {new_face} with {existing_face}")
                try:
                    verification = DeepFace.verify(
                        img1_path=new_face,
                        img2_path=existing_face,
                        enforce_detection=False,
                        detector_backend='dlib',
                        model_name='Facenet512',
                        threshold=0.35
                    )
                    print(verification)

                    if verification['verified']:
                        is_unique = False
                        print(f"Duplicate found, marking existing face for removal: {existing_face}")

                        # Update the map for existing_face
                        face_to_original_image_map[new_face].extend(face_to_original_image_map[existing_face])
                        face_to_original_image_map[new_face] = list(
                            set(face_to_original_image_map[new_face]))  # Ensure uniqueness

                        print(f" for face {new_face} these are the linked images {face_to_original_image_map[new_face]}")
                        # Mark existing_face for removal
                        faces_to_remove.add(existing_face)
                        os.remove(existing_face)  # Remove existing face from filesystem

                except Exception as ve:
                    print(f"Error verifying {new_face} and {existing_face}: {ve}")

            # Add new_face to unique_new_faces if it wasn't marked for removal
            if is_unique:
                unique_new_faces.append(new_face)

        # Remove marked faces from the face_images list and delete the files
        for face in faces_to_remove:
            if face in face_images:
                face_images.remove(face)

        print(f"Unique new faces: {unique_new_faces}")

        # Ensure face_images only contains files that exist
        face_images = [face for face in face_images if os.path.exists(face)]

        face_images = list(set(face_images))
        print(f"Face images after processing {face_images}")
        # Update SQLite with unique new faces
        existing_faces = []
        for face_path in face_images:
            if os.path.exists(face_path):  # Check if the file exists
                original_images = face_to_original_image_map[face_path]
                images_linked = ', '.join(original_images)  # Assuming images_linked should be a comma-separated string

                self.insert_face_data(face_path, images_linked)
                print(f"Inserted {face_path}")

                existing_faces.append(face_path)  # Add only existing faces to the list
            else:
                print(f"File not found for {face_path}, skipping database insertion and processing.")

        # Update face_images list and save processed data
        face_images.extend(existing_faces)
        face_images = list(set(face_images))  # Ensure uniqueness
        self.save_processed_data(face_images, all_images, face_to_original_image_map)
        print(face_images)

        return face_images, all_images

    def get_related_images(self, face_id: str) -> Tuple[List[str], str]:
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            face_filename = f'detected_face_{face_id}.jpg'
            face_path = os.path.join(self.faces_dir, face_filename)
            print(face_path)
            cursor.execute('SELECT images_linked FROM faces WHERE image_id = ?', (face_path,))
            result = cursor.fetchone()
            if result:
                images_linked = result[0].split(', ')  # Assuming images are stored as a comma-separated string
                print(images_linked)
                return images_linked, face_id
            return [], face_id  # Return empty list if no images linked


