import os
import torch
import open_clip
import numpy as np
from PIL import Image
from io import BytesIO
import chromadb
from typing import List, Dict, Optional, Tuple, Any
import logging
from flask import current_app
from sqlalchemy import select

logger = logging.getLogger(__name__)

class VectorService:
    # OpenCLIP ViT-L/14 produces 768-dim embeddings (upgraded from 512-dim ViT-B/32)
    CLIP_EMBEDDING_DIM = 768
    MODEL_NAME = 'ViT-L-14'
    MODEL_PRETRAINED = 'laion2b_s32b_b82k'  # LAION-2B trained weights

    def __init__(self):
        self.device = self._get_optimal_device()
        self.model = None
        self.preprocessor = None
        self.tokenizer = None
        self.chroma_client = None  # Keep for backward compatibility during migration
        self.image_collection = None
        self.face_collection = None
        self.vector_db_type = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure the service is initialized with Flask app context"""
        if not self._initialized:
            self.vector_db_type = current_app.config.get('VECTOR_DB_TYPE', 'chromadb').lower()
            self._initialize_clip_model()
            if self.vector_db_type == 'chromadb':
                self._initialize_chroma_db()
            self._initialized = True

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
            logger.info(f"Initializing OpenCLIP model: {self.MODEL_NAME} with {self.MODEL_PRETRAINED} weights...")

            # Create model and transforms using OpenCLIP
            self.model, _, self.preprocessor = open_clip.create_model_and_transforms(
                self.MODEL_NAME,
                pretrained=self.MODEL_PRETRAINED,
                device=self.device
            )

            # Get tokenizer for text encoding
            self.tokenizer = open_clip.get_tokenizer(self.MODEL_NAME)

            # Set model to evaluation mode
            self.model.eval()

            logger.info(f"✅ OpenCLIP model initialized successfully: {self.MODEL_NAME} ({self.CLIP_EMBEDDING_DIM}-dim embeddings)")
        except Exception as e:
            logger.error(f"Failed to initialize OpenCLIP model: {str(e)}")
            raise Exception(f"OpenCLIP model initialization failed: {str(e)}")
    
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
        """Generate OpenCLIP embedding for an image.

        Args:
            image_data: Raw image bytes

        Returns:
            numpy array of shape (768,) containing the embedding for ViT-L/14

        Raises:
            Exception: If embedding generation fails
        """
        self._ensure_initialized()
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                image_input = self.preprocessor(img).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    embedding = self.model.encode_image(image_input)
                    # Normalize the embedding
                    embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                    embedding = embedding.cpu().numpy().flatten()

                # Validate embedding dimension
                if embedding.shape[0] != self.CLIP_EMBEDDING_DIM:
                    raise ValueError(f"Invalid embedding dimension: {embedding.shape[0]}, expected {self.CLIP_EMBEDDING_DIM}")

                return embedding
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {str(e)}")
            raise Exception(f"Image embedding generation failed: {str(e)}")
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate OpenCLIP embedding for text.

        Args:
            text: Text query string

        Returns:
            numpy array of shape (768,) containing the embedding for ViT-L/14

        Raises:
            Exception: If embedding generation fails
        """
        self._ensure_initialized()
        try:
            # Tokenize text using OpenCLIP tokenizer
            text_input = self.tokenizer([text]).to(self.device)

            with torch.no_grad():
                # Encode text using OpenCLIP model
                embedding = self.model.encode_text(text_input)
                # Normalize the embedding (L2 normalization for cosine similarity)
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                embedding = embedding.cpu().numpy().flatten()

            # Validate embedding dimension
            if embedding.shape[0] != self.CLIP_EMBEDDING_DIM:
                raise ValueError(f"Invalid embedding dimension: {embedding.shape[0]}, expected {self.CLIP_EMBEDDING_DIM}")

            return embedding
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {str(e)}")
            raise Exception(f"Text embedding generation failed: {str(e)}")
    
    def store_image_vector(self, image_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        self._ensure_initialized()
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
        self._ensure_initialized()
        try:
            from models.face import Face

            face = Face.query.filter_by(face_id=face_id).first()
            if not face:
                logger.error(f"Face {face_id} not found while storing embedding")
                return False

            face.set_embedding(embedding)

            if self.vector_db_type == 'pgvector':
                # Persist optional metadata fields when provided
                if metadata:
                    if 'confidence_score' in metadata and face.confidence_score is None:
                        face.confidence_score = metadata['confidence_score']
                    if 'quality_score' in metadata and face.quality_score is None:
                        face.quality_score = metadata['quality_score']

                return True

            if not self.face_collection:
                logger.error("Chroma face collection is not initialized")
                return False

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
        self._ensure_initialized()
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
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity: 1 = identical, 0 = opposite
                similarity = 1 - (distance / 2.0)

                # Apply threshold (higher threshold = stricter matching)
                if similarity >= similarity_threshold:
                    similar_images.append({
                        'id': img_id,
                        'similarity': float(similarity),
                        'distance': float(distance),
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
        self._ensure_initialized()
        try:
            if self.vector_db_type == 'pgvector':
                from models.face import Face

                user_id = None
                if filter_metadata:
                    user_id = filter_metadata.get('user_id')

                results = Face.search_by_embedding(
                    query_embedding=query_embedding.tolist(),
                    user_id=user_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold
                )

                formatted_results: List[Dict[str, Any]] = []
                for face, similarity in results:
                    distance = 2 * (1 - similarity)
                    metadata = {
                        'image_id': face.image_id,
                        'modern_image_id': face.modern_image_id,
                        'confidence_score': face.confidence_score,
                        'quality_score': face.quality_score,
                        'person_id': face.person_id
                    }
                    formatted_results.append({
                        'id': face.face_id,
                        'similarity': float(similarity),
                        'distance': float(distance),
                        'metadata': metadata
                    })

                return formatted_results

            where_clause = filter_metadata if filter_metadata else None

            if not self.face_collection:
                logger.error("Chroma face collection is not initialized")
                return []

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
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity: 1 = identical, 0 = opposite
                similarity = 1 - (distance / 2.0)

                # Apply threshold (higher threshold = stricter matching)
                if similarity >= similarity_threshold:
                    similar_faces.append({
                        'id': face_id,
                        'similarity': float(similarity),
                        'distance': float(distance),
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
        self._ensure_initialized()
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

    # ==================== pgvector Methods (New) ====================

    def store_embedding_to_db(self, image_id: int, embedding: np.ndarray) -> bool:
        """
        Store embedding directly to PostgreSQL using pgvector.

        Args:
            image_id: ModernImage ID (integer)
            embedding: 768-dim numpy array

        Returns:
            True if successful, False otherwise
        """
        try:
            from models.modern_image import ModernImage
            from extensions import db

            image = ModernImage.query.get(image_id)
            if not image:
                logger.error(f"Image {image_id} not found")
                return False

            # Store embedding in pgvector column
            image.embedding = embedding.tolist()
            image.embedding_model = self.MODEL_NAME
            image.embedding_version = 'v3'  # v3 = pgvector with ViT-L/14

            db.session.commit()
            logger.info(f"✅ Stored {self.CLIP_EMBEDDING_DIM}-dim embedding for image {image_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store embedding to DB: {str(e)}")
            try:
                from extensions import db
                db.session.rollback()
            except:
                pass
            return False

    def search_images_pgvector(self,
                               query_embedding: np.ndarray,
                               user_id: Optional[int] = None,
                               limit: int = 20,
                               similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search images using pgvector similarity search.

        Args:
            query_embedding: 768-dim query vector
            user_id: Optional user ID filter
            limit: Maximum results
            similarity_threshold: Minimum similarity (0-1)

        Returns:
            List of dicts with image info and similarity scores
        """
        try:
            from models.modern_image import ModernImage

            # Use the model's search_by_embedding method
            results = ModernImage.search_by_embedding(
                query_embedding=query_embedding.tolist(),
                user_id=user_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            # Format results
            formatted_results = []
            for image, similarity in results:
                formatted_results.append({
                    'id': str(image.id),  # Convert to string for compatibility
                    'similarity': float(similarity),
                    'metadata': {
                        'filename': image.filename,
                        'user_id': image.user_id,
                        'created_at': image.created_at.isoformat(),
                        'location': image.location,
                        'has_faces': image.has_faces
                    }
                })

            logger.info(f"pgvector search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search images with pgvector: {str(e)}")
            return []

    def text_to_image_search_pgvector(self,
                                     text_query: str,
                                     user_id: Optional[int] = None,
                                     limit: int = 20,
                                     similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Text-to-image search using pgvector (recommended method).

        Args:
            text_query: Text search query
            user_id: Optional user ID filter
            limit: Maximum results
            similarity_threshold: Minimum similarity

        Returns:
            List of similar images with scores
        """
        try:
            # Generate text embedding with ViT-L/14
            text_embedding = self.generate_text_embedding(text_query)

            # Search using pgvector
            return self.search_images_pgvector(
                text_embedding,
                user_id=user_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
        except Exception as e:
            logger.error(f"Failed text-to-image search with pgvector: {str(e)}")
            return []
