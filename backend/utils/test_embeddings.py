"""
Utility script to test and validate embeddings functionality.

This script helps diagnose and fix issues with:
- CLIP model initialization
- Embedding generation
- Vector database storage and retrieval
- Search functionality
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from extensions import db
from config.settings import Config
from services.vector_service import VectorService
from models.image import Image
from models.modern_image import ModernImage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    return app


def test_vector_service_initialization():
    """Test 1: VectorService initialization."""
    print("\n" + "="*60)
    print("TEST 1: VectorService Initialization")
    print("="*60)

    try:
        vector_service = VectorService()
        logger.info("✓ VectorService instance created")

        # Force initialization
        vector_service._ensure_initialized()
        logger.info("✓ VectorService initialized successfully")

        # Check components
        assert vector_service.model is not None, "CLIP model not loaded"
        logger.info("✓ CLIP model loaded")

        assert vector_service.preprocessor is not None, "Preprocessor not loaded"
        logger.info("✓ Preprocessor loaded")

        assert vector_service.chroma_client is not None, "ChromaDB client not initialized"
        logger.info("✓ ChromaDB client initialized")

        assert vector_service.image_collection is not None, "Image collection not created"
        logger.info("✓ Image collection created")

        logger.info(f"Device: {vector_service.device}")

        print("\n✅ TEST 1 PASSED: VectorService initialized successfully")
        return vector_service

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {str(e)}")
        raise


def test_text_embedding_generation(vector_service):
    """Test 2: Text embedding generation."""
    print("\n" + "="*60)
    print("TEST 2: Text Embedding Generation")
    print("="*60)

    try:
        test_queries = [
            "a sunset over the ocean",
            "a cat sitting on a chair",
            "mountains covered in snow"
        ]

        for query in test_queries:
            embedding = vector_service.generate_text_embedding(query)
            logger.info(f"✓ Generated embedding for: '{query}'")
            logger.info(f"  - Shape: {embedding.shape}")
            logger.info(f"  - Dtype: {embedding.dtype}")
            logger.info(f"  - Min: {embedding.min():.6f}, Max: {embedding.max():.6f}")
            logger.info(f"  - Norm: {(embedding ** 2).sum() ** 0.5:.6f}")

            assert embedding.shape[0] == VectorService.CLIP_EMBEDDING_DIM, \
                f"Invalid embedding dimension: {embedding.shape[0]}"

        print("\n✅ TEST 2 PASSED: Text embeddings generated successfully")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {str(e)}")
        raise


def test_image_embedding_generation(vector_service):
    """Test 3: Image embedding generation."""
    print("\n" + "="*60)
    print("TEST 3: Image Embedding Generation")
    print("="*60)

    try:
        # Create a simple test image
        from PIL import Image as PILImage
        from io import BytesIO
        import numpy as np

        # Create a 100x100 RGB test image
        test_image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_image = PILImage.fromarray(test_image_array)

        # Convert to bytes
        img_bytes = BytesIO()
        test_image.save(img_bytes, format='PNG')
        image_data = img_bytes.getvalue()

        logger.info("Created test image (100x100 RGB)")

        # Generate embedding
        embedding = vector_service.generate_image_embedding(image_data)

        logger.info(f"✓ Generated embedding for test image")
        logger.info(f"  - Shape: {embedding.shape}")
        logger.info(f"  - Dtype: {embedding.dtype}")
        logger.info(f"  - Min: {embedding.min():.6f}, Max: {embedding.max():.6f}")
        logger.info(f"  - Norm: {(embedding ** 2).sum() ** 0.5:.6f}")

        assert embedding.shape[0] == VectorService.CLIP_EMBEDDING_DIM, \
            f"Invalid embedding dimension: {embedding.shape[0]}"

        print("\n✅ TEST 3 PASSED: Image embeddings generated successfully")
        return embedding, image_data

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {str(e)}")
        raise


def test_vector_storage_and_retrieval(vector_service, embedding):
    """Test 4: Vector storage and retrieval."""
    print("\n" + "="*60)
    print("TEST 4: Vector Storage and Retrieval")
    print("="*60)

    try:
        test_id = "test_image_001"
        test_metadata = {
            'user_id': 999,
            'filename': 'test_image.png',
            'test': True
        }

        # Store vector
        success = vector_service.store_image_vector(test_id, embedding, test_metadata)
        assert success, "Failed to store vector"
        logger.info(f"✓ Stored vector with ID: {test_id}")

        # Retrieve vector
        result = vector_service.get_image_by_id(test_id)
        assert result is not None, "Failed to retrieve vector"
        assert result['id'] == test_id, "ID mismatch"
        logger.info(f"✓ Retrieved vector successfully")
        logger.info(f"  - Metadata: {result['metadata']}")

        # Clean up
        vector_service.remove_image_vector(test_id)
        logger.info(f"✓ Cleaned up test vector")

        print("\n✅ TEST 4 PASSED: Vector storage and retrieval working")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {str(e)}")
        # Clean up on failure
        try:
            vector_service.remove_image_vector("test_image_001")
        except:
            pass
        raise


def test_semantic_search(vector_service):
    """Test 5: Semantic search functionality."""
    print("\n" + "="*60)
    print("TEST 5: Semantic Search")
    print("="*60)

    try:
        from PIL import Image as PILImage
        from io import BytesIO
        import numpy as np

        # Create and store multiple test vectors
        test_vectors = []
        for i in range(5):
            # Create different test images
            test_image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            test_image = PILImage.fromarray(test_image_array)

            img_bytes = BytesIO()
            test_image.save(img_bytes, format='PNG')
            image_data = img_bytes.getvalue()

            embedding = vector_service.generate_image_embedding(image_data)

            test_id = f"search_test_{i}"
            metadata = {
                'user_id': 999,
                'filename': f'test_{i}.png',
                'index': i
            }

            vector_service.store_image_vector(test_id, embedding, metadata)
            test_vectors.append((test_id, embedding))
            logger.info(f"✓ Stored test vector {i}")

        # Perform search with first vector
        query_embedding = test_vectors[0][1]
        results = vector_service.search_similar_images(
            query_embedding,
            limit=5,
            similarity_threshold=0.0  # Low threshold to get all results
        )

        logger.info(f"✓ Search returned {len(results)} results")

        for idx, result in enumerate(results):
            logger.info(f"  Result {idx + 1}:")
            logger.info(f"    - ID: {result['id']}")
            logger.info(f"    - Similarity: {result['similarity']:.4f}")
            logger.info(f"    - Distance: {result.get('distance', 'N/A')}")

        # The first result should be the query image itself
        assert len(results) > 0, "No search results returned"
        assert results[0]['id'] == test_vectors[0][0], "Top result should be query image"
        assert results[0]['similarity'] >= 0.95, "Query image should have high similarity to itself"

        logger.info("✓ Search results validated")

        # Clean up
        for test_id, _ in test_vectors:
            vector_service.remove_image_vector(test_id)
        logger.info("✓ Cleaned up test vectors")

        print("\n✅ TEST 5 PASSED: Semantic search working correctly")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {str(e)}")
        # Clean up on failure
        try:
            for i in range(5):
                vector_service.remove_image_vector(f"search_test_{i}")
        except:
            pass
        raise


def test_text_to_image_search(vector_service):
    """Test 6: Text-to-image search."""
    print("\n" + "="*60)
    print("TEST 6: Text-to-Image Search")
    print("="*60)

    try:
        from PIL import Image as PILImage
        from io import BytesIO
        import numpy as np

        # Create and store a test image
        test_image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_image = PILImage.fromarray(test_image_array)

        img_bytes = BytesIO()
        test_image.save(img_bytes, format='PNG')
        image_data = img_bytes.getvalue()

        embedding = vector_service.generate_image_embedding(image_data)

        test_id = "text_search_test"
        metadata = {'user_id': 999, 'filename': 'test.png'}

        vector_service.store_image_vector(test_id, embedding, metadata)
        logger.info("✓ Stored test image")

        # Perform text-to-image search
        query = "a random image"
        results = vector_service.text_to_image_search(
            query,
            limit=5,
            similarity_threshold=0.0
        )

        logger.info(f"✓ Text search for '{query}' returned {len(results)} results")

        if results:
            logger.info(f"  Top result:")
            logger.info(f"    - ID: {results[0]['id']}")
            logger.info(f"    - Similarity: {results[0]['similarity']:.4f}")

        # Clean up
        vector_service.remove_image_vector(test_id)
        logger.info("✓ Cleaned up test vector")

        print("\n✅ TEST 6 PASSED: Text-to-image search working")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 6 FAILED: {str(e)}")
        # Clean up on failure
        try:
            vector_service.remove_image_vector("text_search_test")
        except:
            pass
        raise


def test_collection_stats(vector_service):
    """Test 7: Collection statistics."""
    print("\n" + "="*60)
    print("TEST 7: Collection Statistics")
    print("="*60)

    try:
        stats = vector_service.get_collection_stats()

        logger.info("Collection Statistics:")
        logger.info(f"  - Image vectors: {stats['image_vectors']}")
        logger.info(f"  - Face vectors: {stats['face_vectors']}")
        logger.info(f"  - Total vectors: {stats['total_vectors']}")
        logger.info(f"  - Device: {stats['device']}")
        logger.info(f"  - Model loaded: {stats['model_loaded']}")

        assert isinstance(stats['image_vectors'], int), "Invalid image_vectors count"
        assert isinstance(stats['face_vectors'], int), "Invalid face_vectors count"
        assert stats['model_loaded'] is True, "Model not loaded"

        print("\n✅ TEST 7 PASSED: Collection stats working")
        return stats

    except Exception as e:
        logger.error(f"❌ TEST 7 FAILED: {str(e)}")
        raise


def test_health_check(vector_service):
    """Test 8: Health check."""
    print("\n" + "="*60)
    print("TEST 8: Health Check")
    print("="*60)

    try:
        health = vector_service.health_check()

        logger.info("Health Check Results:")
        logger.info(f"  - Healthy: {health['healthy']}")
        logger.info(f"  - Model loaded: {health['model_loaded']}")
        logger.info(f"  - Database connected: {health['database_connected']}")
        logger.info(f"  - Device: {health['device']}")
        logger.info(f"  - Image vectors: {health['image_vectors']}")
        logger.info(f"  - Face vectors: {health['face_vectors']}")

        assert health['healthy'] is True, "Health check failed"
        assert health['model_loaded'] is True, "Model not loaded"
        assert health['database_connected'] is True, "Database not connected"

        print("\n✅ TEST 8 PASSED: System healthy")
        return health

    except Exception as e:
        logger.error(f"❌ TEST 8 FAILED: {str(e)}")
        raise


def run_all_tests():
    """Run all embedding tests."""
    print("\n" + "="*60)
    print("EMBEDDINGS TEST SUITE")
    print("="*60)
    print("\nThis will test the following:")
    print("1. VectorService initialization")
    print("2. Text embedding generation")
    print("3. Image embedding generation")
    print("4. Vector storage and retrieval")
    print("5. Semantic search")
    print("6. Text-to-image search")
    print("7. Collection statistics")
    print("8. Health check")
    print("\n" + "="*60)

    app = create_test_app()

    with app.app_context():
        try:
            # Run tests
            vector_service = test_vector_service_initialization()
            test_text_embedding_generation(vector_service)
            embedding, image_data = test_image_embedding_generation(vector_service)
            test_vector_storage_and_retrieval(vector_service, embedding)
            test_semantic_search(vector_service)
            test_text_to_image_search(vector_service)
            test_collection_stats(vector_service)
            test_health_check(vector_service)

            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
            print("\nYour embeddings system is working correctly.")
            print("\nNext steps:")
            print("1. Upload images through the API")
            print("2. Test search functionality in the frontend")
            print("3. Monitor logs for any issues")

            return True

        except Exception as e:
            print("\n" + "="*60)
            print("❌ TESTS FAILED!")
            print("="*60)
            print(f"\nError: {str(e)}")
            print("\nTroubleshooting:")
            print("1. Check that CLIP is installed: pip install git+https://github.com/openai/CLIP.git")
            print("2. Check that ChromaDB is installed: pip install chromadb")
            print("3. Check that PyTorch is installed: pip install torch torchvision")
            print("4. Check CHROMADB_PATH in .env file")
            print("5. Check file permissions for ChromaDB directory")

            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test embeddings functionality")
    parser.add_argument("--test", type=str, help="Run specific test (1-8)")
    args = parser.parse_args()

    if args.test:
        # Run specific test
        app = create_test_app()
        with app.app_context():
            vector_service = test_vector_service_initialization()

            if args.test == "2":
                test_text_embedding_generation(vector_service)
            elif args.test == "3":
                test_image_embedding_generation(vector_service)
            elif args.test == "4":
                embedding, _ = test_image_embedding_generation(vector_service)
                test_vector_storage_and_retrieval(vector_service, embedding)
            elif args.test == "5":
                test_semantic_search(vector_service)
            elif args.test == "6":
                test_text_to_image_search(vector_service)
            elif args.test == "7":
                test_collection_stats(vector_service)
            elif args.test == "8":
                test_health_check(vector_service)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
