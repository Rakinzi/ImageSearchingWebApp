"""
Modern Image Service with enhanced functionality and async patterns.
"""
from __future__ import annotations

import os
import logging
from collections import OrderedDict
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
import structlog

from models.modern_image import ModernImage, ImageStatus
from models.face import Face
from services.vector_service import VectorService
from utils.helpers import (
    validate_and_process_image,
    create_directory_structure,
    extract_exif_data,
    extract_gps_coordinates,
    reverse_geocode,
    extract_date_from_exif
)
from utils.security import generate_secure_filename, calculate_file_hash
from extensions import db

logger = structlog.get_logger(__name__)


class ModernImageService:
    """
    Modern Image Service with enhanced functionality.

    Features:
    - Async processing patterns
    - Advanced search capabilities
    - Comprehensive error handling
    - Metrics and analytics
    - File lifecycle management
    """

    def __init__(self):
        self.vector_service = VectorService()
        self.upload_base_path = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure the service is initialized with Flask app context"""
        if not self._initialized:
            self.upload_base_path = Path(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'))
            self._initialized = True

    def create_image_record(
        self,
        file: FileStorage,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ModernImage]:
        """
        Create a new image record from uploaded file.

        Args:
            file: Uploaded file storage object
            user_id: ID of the user uploading the image
            metadata: Optional additional metadata

        Returns:
            Created ModernImage instance or None if creation failed
        """
        self._ensure_initialized()
        try:
            # Validate file
            if not self._validate_upload_file(file):
                logger.warning("Invalid file upload attempted",
                              user_id=user_id,
                              filename=file.filename)
                return None

            # Calculate file hash
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            checksum = calculate_file_hash(file_content)

            # Check for duplicates
            existing_image = ModernImage.find_by_checksum(checksum, user_id)
            if existing_image:
                logger.info("Duplicate image detected",
                           user_id=user_id,
                           existing_image_id=existing_image.id,
                           filename=file.filename)
                return existing_image

            # Generate secure filename
            secure_filename = generate_secure_filename(file.filename)
            user_paths = self._create_user_directories(user_id)

            # Save file
            file_path = user_paths['images'] / secure_filename
            file.save(str(file_path))

            # Extract basic image properties
            image_props = self._extract_image_properties(file_path)

            # Extract EXIF data
            exif_data = extract_exif_data(str(file_path))
            image_date = extract_date_from_exif(exif_data) if exif_data else None

            # Extract GPS coordinates and reverse geocode
            location = None
            if exif_data:
                coordinates = extract_gps_coordinates(exif_data)
                if coordinates:
                    location = reverse_geocode(coordinates['latitude'], coordinates['longitude'])

            # Create database record
            image = ModernImage(
                filename=secure_filename,
                original_filename=file.filename,
                file_path=str(file_path.relative_to(self.upload_base_path)),
                file_size=len(file_content),
                mime_type=file.content_type or 'application/octet-stream',
                width=image_props.get('width'),
                height=image_props.get('height'),
                checksum=checksum,
                status=ImageStatus.PENDING,
                image_date=image_date,
                location=location,
                exif_data=exif_data,
                image_metadata=metadata or {},
                user_id=user_id
            )

            db.session.add(image)
            db.session.commit()

            # Generate thumbnail immediately so users can see it right away
            # This happens synchronously before queuing async processing
            try:
                thumbnail_path = self._generate_thumbnail(image, file_path)
                if thumbnail_path:
                    image.thumbnail_path = str(thumbnail_path.relative_to(self.upload_base_path))
                    db.session.commit()
                    logger.info("Thumbnail generated immediately after upload",
                               image_id=image.id,
                               thumbnail_path=image.thumbnail_path)
            except Exception as thumb_error:
                logger.warning("Failed to generate thumbnail immediately",
                              image_id=image.id,
                              error=str(thumb_error))
                # Don't fail the upload if thumbnail generation fails

            logger.info("Image record created successfully",
                       user_id=user_id,
                       image_id=image.id,
                       filename=secure_filename,
                       file_size=len(file_content))

            return image

        except Exception as e:
            logger.error("Failed to create image record",
                        user_id=user_id,
                        filename=file.filename,
                        error=str(e),
                        error_type=type(e).__name__)
            db.session.rollback()
            return None

    def search_images(
        self,
        query: str,
        user_id: int,
        search_type: str = 'semantic',
        limit: int = 20,
        similarity_threshold: float = 0.8,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ModernImage, float]]:
        """
        Advanced image search with multiple search types.

        Args:
            query: Search query
            user_id: User ID to search within
            search_type: Type of search ('semantic', 'text', 'metadata', 'hybrid')
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            filters: Additional filters

        Returns:
            List of tuples containing (image, similarity_score)
        """
        try:
            person_results: List[Tuple[ModernImage, float]] = []
            base_results: List[Tuple[ModernImage, float]] = []
            if query and query.strip():
                person_results = self._person_name_search(query, user_id, limit)

            if search_type == 'semantic':
                base_results = self._semantic_search(query, user_id, limit, similarity_threshold)
            elif search_type == 'text':
                base_results = self._text_search(query, user_id, limit)
            elif search_type == 'metadata':
                base_results = self._metadata_search(query, user_id, limit, filters)
            elif search_type == 'hybrid':
                base_results = self._hybrid_search(query, user_id, limit, similarity_threshold, filters)
            elif search_type == 'person':
                return person_results[:limit]
            else:
                raise ValueError(f"Unsupported search type: {search_type}")

            if person_results:
                return self._merge_results(person_results, base_results, limit)

            return base_results

        except Exception as e:
            logger.error("Image search failed",
                        user_id=user_id,
                        query=query,
                        search_type=search_type,
                        error=str(e))
            return []

    def delete_image(self, image: ModernImage) -> bool:
        """
        Completely delete an image and all associated data.

        Args:
            image: Image to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Delete from vector database
            if image.vector_id:
                self.vector_service.remove_image_vector(image.vector_id)

            # Delete physical files
            self._delete_image_files(image)

            # Delete database record (cascade will handle related data)
            db.session.delete(image)
            db.session.commit()

            logger.info("Image deleted successfully",
                       image_id=image.id,
                       user_id=image.user_id,
                       filename=image.filename)

            return True

        except Exception as e:
            logger.error("Failed to delete image",
                        image_id=image.id,
                        user_id=image.user_id,
                        error=str(e))
            db.session.rollback()
            return False

    def process_image_content(
        self,
        image: ModernImage,
        extract_text: bool = True,
        detect_faces: bool = True,
        generate_embeddings: bool = True
    ) -> bool:
        """
        Process image content with configurable options.

        Args:
            image: Image to process
            extract_text: Whether to extract text content
            detect_faces: Whether to detect faces
            generate_embeddings: Whether to generate vector embeddings

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            self._ensure_initialized()
            image.start_processing()

            file_path = self.upload_base_path / image.file_path

            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(image, file_path)
            if thumbnail_path:
                image.thumbnail_path = str(thumbnail_path.relative_to(self.upload_base_path))

            # Extract text content
            if extract_text:
                extracted_text = self._extract_text_content(file_path)
                image.extracted_text = extracted_text

            # Detect faces
            if detect_faces:
                self._detect_and_store_faces(image, file_path)

            # Generate embeddings
            if generate_embeddings:
                vector_id = self._generate_embeddings(image, file_path)
                image.vector_id = vector_id

            # Update image record
            db.session.add(image)
            image.complete_processing()

            logger.info("Image processing completed successfully",
                       image_id=image.id,
                       user_id=image.user_id,
                       processing_time=image.processing_time)

            return True

        except Exception as e:
            logger.error("Image processing failed",
                        image_id=image.id,
                        user_id=image.user_id,
                        error=str(e))

            image.fail_processing(str(e))
            return False

    def get_processing_queue_status(self) -> Dict[str, Any]:
        """Get status of the image processing queue."""
        try:
            pending_count = ModernImage.query.filter_by(status=ImageStatus.PENDING).count()
            processing_count = ModernImage.query.filter_by(status=ImageStatus.PROCESSING).count()
            failed_count = ModernImage.query.filter_by(status=ImageStatus.FAILED).count()

            # Get average processing time
            completed_images = ModernImage.query.filter_by(status=ImageStatus.COMPLETED).all()
            processing_times = [img.processing_time for img in completed_images if img.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            return {
                'pending': pending_count,
                'processing': processing_count,
                'failed': failed_count,
                'avg_processing_time_seconds': avg_processing_time,
                'queue_health': 'healthy' if failed_count < pending_count * 0.1 else 'degraded'
            }

        except Exception as e:
            logger.error("Failed to get queue status", error=str(e))
            return {'error': str(e)}

    # Private methods
    def _validate_upload_file(self, file: FileStorage) -> bool:
        """Validate uploaded file."""
        if not file or not file.filename:
            return False

        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
        file_extension = file.filename.split('.')[-1].lower()

        return file_extension in allowed_extensions

    def _create_user_directories(self, user_id: int) -> Dict[str, Path]:
        """Create directory structure for user."""
        try:
            user_base = self.upload_base_path / str(user_id)
            directories = {
                'base': user_base,
                'images': user_base / 'images',
                'thumbnails': user_base / 'thumbnails',
                'faces': user_base / 'faces'
            }

            for directory in directories.values():
                directory.mkdir(parents=True, exist_ok=True)

            return directories

        except Exception as e:
            logger.error("Failed to create user directories",
                        user_id=user_id,
                        error=str(e))
            raise

    def _extract_image_properties(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic image properties using PIL."""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception as e:
            logger.warning("Failed to extract image properties",
                          file_path=str(file_path),
                          error=str(e))
            return {}

    def _semantic_search(
        self,
        query: str,
        user_id: int,
        limit: int,
        similarity_threshold: float
    ) -> List[Tuple[ModernImage, float]]:
        """Perform semantic search using pgvector embeddings."""
        try:
            # Generate text embedding for the search query
            query_embedding = self.vector_service.generate_text_embedding(query)

            # Search using pgvector (not ChromaDB)
            results = self.vector_service.text_to_image_search_pgvector(
                text_query=query,
                user_id=user_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            # Convert results to (image, score) tuples
            image_results = []
            for result in results:
                image_id = int(result['id'])
                similarity = result['similarity']

                image = ModernImage.query.get(image_id)
                if image and image.user_id == user_id:
                    image_results.append((image, similarity))

            logger.info("Semantic search completed",
                       query=query,
                       results_count=len(image_results))

            return image_results

        except Exception as e:
            logger.error("Semantic search failed",
                        query=query,
                        user_id=user_id,
                        error=str(e))
            return []

    def _text_search(self, query: str, user_id: int, limit: int) -> List[Tuple[ModernImage, float]]:
        """Search extracted text content."""
        images = ModernImage.query.filter(
            ModernImage.user_id == user_id,
            ModernImage.extracted_text.like(f'%{query}%'),
            ModernImage.status == ImageStatus.COMPLETED
        ).limit(limit).all()

        # Return with placeholder similarity scores
        return [(image, 1.0) for image in images]

    def _person_name_search(
        self,
        query: str,
        user_id: int,
        limit: int
    ) -> List[Tuple[ModernImage, float]]:
        """
        Search images by manually assigned face labels (person names).
        Returns images that contain faces matching all query terms.
        """
        try:
            search_terms = [term.strip() for term in query.split() if term.strip()]
            if not search_terms:
                return []

            images_query = ModernImage.query.filter(
                ModernImage.user_id == user_id,
                ModernImage.status == ImageStatus.COMPLETED
            )

            for term in search_terms:
                images_query = images_query.filter(
                    ModernImage.faces.any(Face.person_name.ilike(f'%{term}%'))
                )

            images = images_query.order_by(ModernImage.created_at.desc()).limit(limit).all()
            return [(image, 1.0) for image in images]

        except Exception as e:
            logger.warning("Person name search failed",
                           query=query,
                           user_id=user_id,
                           error=str(e))
            return []

    def _metadata_search(
        self,
        query: str,
        user_id: int,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ModernImage, float]]:
        """Search metadata and EXIF data."""
        # Simple metadata search - can be enhanced with more sophisticated querying
        images = ModernImage.query.filter(
            ModernImage.user_id == user_id,
            ModernImage.status == ImageStatus.COMPLETED
        )

        if filters:
            if 'location' in filters:
                images = images.filter(ModernImage.location.like(f'%{filters["location"]}%'))

        images = images.limit(limit).all()
        return [(image, 1.0) for image in images]

    def _hybrid_search(
        self,
        query: str,
        user_id: int,
        limit: int,
        similarity_threshold: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ModernImage, float]]:
        """Combine multiple search types."""
        # Combine results from different search types
        semantic_results = self._semantic_search(query, user_id, limit // 2, similarity_threshold)
        text_results = self._text_search(query, user_id, limit // 2)

        # Merge and deduplicate results
        all_results = {}
        for image, score in semantic_results + text_results:
            if image.id in all_results:
                # Take higher score
                all_results[image.id] = (image, max(all_results[image.id][1], score))
            else:
                all_results[image.id] = (image, score)

        # Sort by score and return top results
        sorted_results = sorted(all_results.values(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]

    def _merge_results(
        self,
        primary: List[Tuple[ModernImage, float]],
        secondary: List[Tuple[ModernImage, float]],
        limit: int
    ) -> List[Tuple[ModernImage, float]]:
        """Merge two result lists, preserving order and highest score per image."""
        combined: "OrderedDict[int, Tuple[ModernImage, float]]" = OrderedDict()

        for image, score in primary:
            combined[image.id] = (image, score)

        for image, score in secondary:
            existing = combined.get(image.id)
            if existing:
                if score > existing[1]:
                    combined[image.id] = (image, score)
            else:
                combined[image.id] = (image, score)

        return list(combined.values())[:limit]

    def _generate_thumbnail(self, image: ModernImage, file_path: Path) -> Optional[Path]:
        """Generate thumbnail for image with fixed dimensions (center crop)."""
        try:
            from PIL import Image, ImageOps
            thumbnail_size = current_app.config.get('THUMBNAIL_SIZE', (300, 300))
            quality = current_app.config.get('THUMBNAIL_QUALITY', 85)

            user_paths = self._create_user_directories(image.user_id)
            thumbnail_path = user_paths['thumbnails'] / f"thumb_{image.filename}"

            with Image.open(file_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Use ImageOps.fit to create a fixed-size thumbnail with center cropping
                # This ensures all thumbnails have exactly the same dimensions
                thumbnail = ImageOps.fit(
                    img,
                    thumbnail_size,
                    Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5)  # Center crop
                )

                thumbnail.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)

            logger.info("Thumbnail generated",
                       image_id=image.id,
                       thumbnail_size=thumbnail_size,
                       thumbnail_path=str(thumbnail_path))

            return thumbnail_path

        except Exception as e:
            logger.warning("Failed to generate thumbnail",
                          image_id=image.id,
                          error=str(e))
            return None

    def _extract_text_content(self, file_path: Path) -> Optional[str]:
        """Extract text content from image using OCR."""
        try:
            from utils.ocr import extract_text_from_image

            extracted_text = extract_text_from_image(str(file_path))

            if extracted_text:
                logger.info("Text extracted from image",
                           file_path=str(file_path),
                           text_length=len(extracted_text))
            else:
                logger.debug("No text found in image",
                            file_path=str(file_path))

            return extracted_text

        except Exception as e:
            logger.warning("Failed to extract text content",
                          file_path=str(file_path),
                          error=str(e))
            return None

    def _detect_and_store_faces(self, image: ModernImage, file_path: Path) -> None:
        """Detect faces and store face data directly for modern images."""
        try:
            import cv2
            import numpy as np
            from models.face import Face
            from utils.security import generate_secure_filename

            # Use DeepFace for face detection
            from deepface import DeepFace

            # Detect faces in the image
            try:
                detections = DeepFace.extract_faces(
                    img_path=str(file_path),
                    detector_backend='opencv',
                    enforce_detection=False,
                    align=True
                )
            except Exception as detection_error:
                logger.warning("Face detection failed",
                              image_id=image.id,
                              error=str(detection_error))
                return

            if not detections:
                logger.info("No faces detected in image", image_id=image.id)
                return

            user_paths = self._create_user_directories(image.user_id)
            faces_saved = 0

            for idx, detection in enumerate(detections):
                try:
                    confidence = detection.get('confidence', 0.0)

                    # Skip low confidence detections
                    if confidence < 0.5:
                        continue

                    facial_area = detection.get('facial_area', {})
                    face_img = detection.get('face')

                    if face_img is None or not facial_area:
                        continue

                    # Generate unique face ID and filename
                    face_id = f"face_{image.id}_{idx}_{generate_secure_filename('face.jpg')[:16]}"
                    face_filename = f"{face_id}.jpg"
                    face_path = user_paths['faces'] / face_filename

                    # Convert face image to uint8 if needed
                    if face_img.dtype != np.uint8:
                        face_img = (face_img * 255).astype(np.uint8)

                    # Save face crop
                    cv2.imwrite(str(face_path), cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))

                    # Calculate file checksum
                    with open(face_path, 'rb') as f:
                        from utils.security import calculate_file_hash
                        face_checksum = calculate_file_hash(f.read())

                    # Create Face record with modern_image_id
                    face = Face(
                        face_id=face_id,
                        file_path=str(face_path.relative_to(self.upload_base_path)),
                        checksum=face_checksum,
                        bounding_box=facial_area,
                        confidence_score=float(confidence),
                        status='processed',
                        image_id=None,  # Null for modern images (use modern_image_id instead)
                        modern_image_id=image.id  # Link to ModernImage
                    )

                    db.session.add(face)
                    faces_saved += 1

                except Exception as face_error:
                    logger.warning("Failed to save face",
                                  image_id=image.id,
                                  face_idx=idx,
                                  error=str(face_error))
                    continue

            if faces_saved > 0:
                db.session.commit()
                logger.info("Face detection completed for modern image",
                           image_id=image.id,
                           faces_detected=len(detections),
                           faces_saved=faces_saved)
            else:
                logger.info("No valid faces saved for image", image_id=image.id)

        except Exception as e:
            logger.warning("Failed to detect faces",
                          image_id=image.id,
                          error=str(e))

    def _generate_embeddings(self, image: ModernImage, file_path: Path) -> Optional[str]:
        """Generate vector embeddings for image using pgvector (NOT ChromaDB)."""
        try:
            # Read image file as bytes
            with open(file_path, 'rb') as f:
                image_data = f.read()

            # Generate image embedding using CLIP ViT-L/14 (768 dimensions)
            embedding = self.vector_service.generate_image_embedding(image_data)

            # Store in PostgreSQL using pgvector extension (modern v2 API)
            # This stores the 768-dim embedding directly in the modern_images table
            success = self.vector_service.store_embedding_to_db(
                image_id=image.id,  # Integer ID
                embedding=embedding
            )

            if success:
                logger.info("Embedding stored to pgvector",
                           image_id=image.id,
                           embedding_dim=len(embedding))
                return str(image.id)
            else:
                logger.error("Failed to store embedding to pgvector",
                            image_id=image.id)
                return None

        except Exception as e:
            logger.error("Failed to generate embeddings",
                        image_id=image.id,
                        error=str(e))
            return None

    def _delete_image_files(self, image: ModernImage) -> None:
        """Delete physical image files."""
        try:
            # Delete main image file
            if image.file_path:
                main_file = self.upload_base_path / image.file_path
                if main_file.exists():
                    main_file.unlink()

            # Delete thumbnail
            if image.thumbnail_path:
                thumbnail_file = self.upload_base_path / image.thumbnail_path
                if thumbnail_file.exists():
                    thumbnail_file.unlink()

        except Exception as e:
            logger.warning("Failed to delete image files",
                          image_id=image.id,
                          error=str(e))
