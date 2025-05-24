import os
import torch
import clip
import numpy as np
from PIL import Image
from io import BytesIO
import chromadb
from typing import List, Dict, Optional, Tuple, Any
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.device = self._get_optimal_device()
        self.model = None
        self.preprocessor = None
        self.chroma_client = None
        self.image_collection = None
        self.face_collection = None
        self._initialize_clip_model()
        self._initialize_chroma_db()
    
    def _get_optimal_device(self):
        if torch.cuda.is_available():
            logger.info("Using CUDA device for vector processing")
            return torch.device('cuda')
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Using MPS device for vector processing")
            return torch.device('mps')
        else:
            logger.info("Using CPU device for vector processing")
            return torch.device('cpu')
    
    def _initialize_clip_model(self):
        try:
            logger.info("Initializing CLIP model...")
            self.model, self.preprocessor = clip.load('ViT-B/32', device=self.device)
            self.model.eval()
            logger.info("CLIP model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CLIP model: {str(e)}")
            raise Exception(f"CLIP model initialization failed: {str(e)}")
    
    def _initialize_chroma_db(self):
        try:
            chroma_path = current_app.config.get('CHROMADB_PATH', './chroma_db')
            os.makedirs(chroma_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            self.image_collection = self.chroma_client.get_or_create_collection(
                name='image_vectors',
                metadata={"hnsw:space": "cosine"}
            )
            
            self.face_collection = self.chroma_client.get_or_create_collection(
                name='face_embeddings',
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise Exception(f"ChromaDB initialization failed: {str(e)}")
    
    def generate_image_embedding(self, image_data: bytes) -> np.ndarray:
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                image_input = self.preprocessor(img).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    embedding = self.model.encode_image(image_input)
                    embedding = embedding.cpu().numpy().flatten()
                
                return embedding
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {str(e)}")
            raise Exception(f"Image embedding generation failed: {str(e)}")
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        try:
            text_input = clip.tokenize([text]).to(self.device)
            
            with torch.no_grad():
                embedding = self.model.encode_text(text_input)
                embedding = embedding.cpu().numpy().flatten()
            
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {str(e)}")
            raise Exception(f"Text embedding generation failed: {str(e)}")
    
    def store_image_vector(self, image_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        try:
            self.image_collection.upsert(
                ids=[image_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store image vector: {str(e)}")
            return False
    
    def store_face_vector(self, face_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        try:
            self.face_collection.upsert(
                ids=[face_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store face vector: {str(e)}")
            return False
    
    def search_similar_images(self, query_embedding: np.ndarray, 
                            limit: int = 20, 
                            similarity_threshold: float = 0.85,
                            filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            where_clause = filter_metadata if filter_metadata else None
            
            results = self.image_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=where_clause
            )
            
            if not results['ids'] or not results['ids'][0]:
                return []
            
            similar_images = []
            for i, (img_id, distance, metadata) in enumerate(zip(
                results['ids'][0], 
                results['distances'][0], 
                results['metadatas'][0]
            )):
                similarity = 1 - distance
                if similarity >= (1 - similarity_threshold):
                    similar_images.append({
                        'id': img_id,
                        'similarity': similarity,
                        'metadata': metadata
                    })
            
            return similar_images
        except Exception as e:
            logger.error(f"Failed to search similar images: {str(e)}")
            return []
    
    def search_similar_faces(self, query_embedding: np.ndarray,
                           limit: int = 20,
                           similarity_threshold: float = 0.7,
                           filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            where_clause = filter_metadata if filter_metadata else None
            
            results = self.face_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=where_clause
            )
            
            if not results['ids'] or not results['ids'][0]:
                return []
            
            similar_faces = []
            for i, (face_id, distance, metadata) in enumerate(zip(
                results['ids'][0],
                results['distances'][0],
                results['metadatas'][0]
            )):
                similarity = 1 - distance
                if similarity >= (1 - similarity_threshold):
                    similar_faces.append({
                        'id': face_id,
                        'similarity': similarity,
                        'metadata': metadata
                    })
            
            return similar_faces
        except Exception as e:
            logger.error(f"Failed to search similar faces: {str(e)}")
            return []
    
    def text_to_image_search(self, text_query: str,
                           limit: int = 20,
                           similarity_threshold: float = 0.85,
                           filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            text_embedding = self.generate_text_embedding(text_query)
            return self.search_similar_images(
                text_embedding, 
                limit, 
                similarity_threshold, 
                filter_metadata
            )
        except Exception as e:
            logger.error(f"Failed to perform text-to-image search: {str(e)}")
            return []
    
    def image_to_image_search(self, image_data: bytes,
                            limit: int = 20,
                            similarity_threshold: float = 0.85,
                            filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            image_embedding = self.generate_image_embedding(image_data)
            return self.search_similar_images(
                image_embedding,
                limit,
                similarity_threshold,
                filter_metadata
            )
        except Exception as e:
            logger.error(f"Failed to perform image-to-image search: {str(e)}")
            return []
    
    def get_image_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.image_collection.get(ids=[image_id])
            if result['ids'] and result['ids'][0]:
                return {
                    'id': result['ids'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else None,
                    'embedding': result['embeddings'][0] if result['embeddings'] else None
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get image by ID: {str(e)}")
            return None
    
    def get_face_by_id(self, face_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.face_collection.get(ids=[face_id])
            if result['ids'] and result['ids'][0]:
                return {
                    'id': result['ids'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else None,
                    'embedding': result['embeddings'][0] if result['embeddings'] else None
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get face by ID: {str(e)}")
            return None
    
    def remove_image_vector(self, image_id: str) -> bool:
        try:
            self.image_collection.delete(ids=[image_id])
            return True
        except Exception as e:
            logger.error(f"Failed to remove image vector: {str(e)}")
            return False
    
    def remove_face_vector(self, face_id: str) -> bool:
        try:
            self.face_collection.delete(ids=[face_id])
            return True
        except Exception as e:
            logger.error(f"Failed to remove face vector: {str(e)}")
            return False
    
    def update_image_metadata(self, image_id: str, metadata: Dict[str, Any]) -> bool:
        try:
            existing = self.get_image_by_id(image_id)
            if existing and existing['embedding']:
                self.image_collection.upsert(
                    ids=[image_id],
                    embeddings=[existing['embedding']],
                    metadatas=[metadata]
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update image metadata: {str(e)}")
            return False
    
    def update_face_metadata(self, face_id: str, metadata: Dict[str, Any]) -> bool:
        try:
            existing = self.get_face_by_id(face_id)
            if existing and existing['embedding']:
                self.face_collection.upsert(
                    ids=[face_id],
                    embeddings=[existing['embedding']],
                    metadatas=[metadata]
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update face metadata: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            image_count = self.image_collection.count()
            face_count = self.face_collection.count()
            
            return {
                'image_vectors': image_count,
                'face_vectors': face_count,
                'total_vectors': image_count + face_count,
                'device': str(self.device),
                'model_loaded': self.model is not None
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                'image_vectors': 0,
                'face_vectors': 0,
                'total_vectors': 0,
                'device': str(self.device),
                'model_loaded': False
            }
    
    def batch_process_images(self, image_data_list: List[Tuple[str, bytes, Dict[str, Any]]]) -> Dict[str, Any]:
        results = {
            'successful': [],
            'failed': []
        }
        
        for image_id, image_data, metadata in image_data_list:
            try:
                embedding = self.generate_image_embedding(image_data)
                if self.store_image_vector(image_id, embedding, metadata):
                    results['successful'].append(image_id)
                else:
                    results['failed'].append({'id': image_id, 'error': 'Failed to store vector'})
            except Exception as e:
                results['failed'].append({'id': image_id, 'error': str(e)})
        
        return results
    
    def batch_process_faces(self, face_data_list: List[Tuple[str, np.ndarray, Dict[str, Any]]]) -> Dict[str, Any]:
        results = {
            'successful': [],
            'failed': []
        }
        
        for face_id, embedding, metadata in face_data_list:
            try:
                if self.store_face_vector(face_id, embedding, metadata):
                    results['successful'].append(face_id)
                else:
                    results['failed'].append({'id': face_id, 'error': 'Failed to store vector'})
            except Exception as e:
                results['failed'].append({'id': face_id, 'error': str(e)})
        
        return results
    
    def cleanup_orphaned_vectors(self, valid_image_ids: List[str], valid_face_ids: List[str]) -> Dict[str, int]:
        try:
            all_image_vectors = self.image_collection.get()
            all_face_vectors = self.face_collection.get()
            
            orphaned_images = []
            orphaned_faces = []
            
            if all_image_vectors['ids']:
                for img_id in all_image_vectors['ids']:
                    if img_id not in valid_image_ids:
                        orphaned_images.append(img_id)
            
            if all_face_vectors['ids']:
                for face_id in all_face_vectors['ids']:
                    if face_id not in valid_face_ids:
                        orphaned_faces.append(face_id)
            
            if orphaned_images:
                self.image_collection.delete(ids=orphaned_images)
            
            if orphaned_faces:
                self.face_collection.delete(ids=orphaned_faces)
            
            return {
                'orphaned_images_removed': len(orphaned_images),
                'orphaned_faces_removed': len(orphaned_faces)
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned vectors: {str(e)}")
            return {'orphaned_images_removed': 0, 'orphaned_faces_removed': 0}
    
    def health_check(self) -> Dict[str, Any]:
        try:
            model_status = self.model is not None
            chroma_status = self.chroma_client is not None
            
            if chroma_status:
                try:
                    image_count = self.image_collection.count()
                    face_count = self.face_collection.count()
                except:
                    image_count = -1
                    face_count = -1
                    chroma_status = False
            else:
                image_count = -1
                face_count = -1
            
            return {
                'healthy': model_status and chroma_status,
                'model_loaded': model_status,
                'database_connected': chroma_status,
                'device': str(self.device),
                'image_vectors': image_count,
                'face_vectors': face_count
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e)
            }