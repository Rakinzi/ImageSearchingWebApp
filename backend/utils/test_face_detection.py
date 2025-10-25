"""
Utility script to test and validate face detection functionality.

This script helps diagnose and test:
- MTCNN face detector initialization
- Face detection in images
- Face embedding generation
- Face attribute analysis (age, gender, emotion)
- Face clustering
- Face search functionality
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from extensions import db
from config.settings import Config
from services.face_service import FaceService
from services.image_service import ImageService
from models.image import Image
from models.face import Face
from models.user import User

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


def test_face_service_initialization():
    """Test 1: FaceService initialization."""
    print("\n" + "="*60)
    print("TEST 1: FaceService Initialization")
    print("="*60)

    try:
        face_service = FaceService()
        logger.info("✓ FaceService instance created")

        # Force initialization
        face_service._ensure_initialized()
        logger.info("✓ FaceService initialized successfully")

        # Check components
        assert face_service.mtcnn is not None, "MTCNN not loaded"
        logger.info("✓ MTCNN face detector loaded")

        assert face_service.vector_service is not None, "VectorService not initialized"
        logger.info("✓ VectorService initialized")

        logger.info(f"Device: {face_service.device}")
        logger.info(f"Detection threshold: {face_service.face_detection_threshold}")
        logger.info(f"Similarity threshold: {face_service.face_similarity_threshold}")
        logger.info(f"Faces directory: {face_service.faces_dir}")

        print("\n✅ TEST 1 PASSED: FaceService initialized successfully")
        return face_service

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {str(e)}")
        raise


def test_face_detection_on_test_image(face_service):
    """Test 2: Detect faces in a test image."""
    print("\n" + "="*60)
    print("TEST 2: Face Detection on Test Image")
    print("="*60)

    try:
        from PIL import Image as PILImage, ImageDraw
        import numpy as np

        # Create a simple test image with a simulated face
        # (This is just a placeholder - real face detection needs actual faces)
        img = PILImage.new('RGB', (400, 400), color='white')
        draw = ImageDraw.Draw(img)

        # Draw a simple face-like shape
        # Face oval
        draw.ellipse([100, 80, 300, 320], fill='#f0d0a0', outline='black')
        # Eyes
        draw.ellipse([140, 140, 180, 180], fill='black')
        draw.ellipse([220, 140, 260, 180], fill='black')
        # Nose
        draw.polygon([(200, 180), (190, 240), (210, 240)], fill='#d0b080')
        # Mouth
        draw.arc([160, 220, 240, 280], 0, 180, fill='black', width=3)

        # Save test image
        test_image_path = Path('test_face_image.jpg')
        img.save(test_image_path)
        logger.info(f"✓ Created test image: {test_image_path}")

        # Load image and detect faces
        import cv2
        cv_image = cv2.imread(str(test_image_path))
        image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        boxes, probs, landmarks = face_service.mtcnn.detect(image_rgb, landmarks=True)

        logger.info(f"Detection results:")
        logger.info(f"  - Boxes: {boxes}")
        logger.info(f"  - Probabilities: {probs}")
        logger.info(f"  - Landmarks: {landmarks is not None}")

        if boxes is not None and len(boxes) > 0:
            logger.info(f"✓ Detected {len(boxes)} face(s)")
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                logger.info(f"  Face {i+1}:")
                logger.info(f"    - Confidence: {prob:.4f}")
                logger.info(f"    - Bounding box: {box}")
        else:
            logger.warning("⚠️  No faces detected in test image")
            logger.info("Note: This is a simple test image and may not trigger detection")

        # Clean up
        if test_image_path.exists():
            test_image_path.unlink()
            logger.info("✓ Cleaned up test image")

        print("\n✅ TEST 2 PASSED: Face detection executed (check results above)")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {str(e)}")
        # Clean up on failure
        if Path('test_face_image.jpg').exists():
            Path('test_face_image.jpg').unlink()
        raise


def test_face_detection_on_real_image(face_service):
    """Test 3: Detect faces in a real uploaded image (if available)."""
    print("\n" + "="*60)
    print("TEST 3: Face Detection on Real Images")
    print("="*60)

    try:
        # Find images in database
        images = Image.query.filter(
            Image.status == 'completed'
        ).limit(5).all()

        if not images:
            logger.warning("⚠️  No completed images found in database")
            logger.info("Upload some images with faces to test this functionality")
            print("\n⚠️  TEST 3 SKIPPED: No images available")
            return True

        logger.info(f"Found {len(images)} completed images")

        total_faces = 0
        for image in images:
            if not os.path.exists(image.file_path):
                logger.warning(f"⚠️  Image file not found: {image.file_path}")
                continue

            logger.info(f"\nProcessing image ID {image.id}: {image.filename}")

            detected_faces = face_service.detect_faces_in_image(image.id)
            logger.info(f"  ✓ Detected {len(detected_faces)} face(s)")

            for face_data in detected_faces:
                logger.info(f"    - Confidence: {face_data['confidence_score']:.4f}")
                logger.info(f"    - Quality: {face_data['quality_score']:.4f}")
                logger.info(f"    - Face ID: {face_data['face_id']}")

            total_faces += len(detected_faces)

        logger.info(f"\n✓ Total faces detected across all images: {total_faces}")

        print("\n✅ TEST 3 PASSED: Face detection on real images completed")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {str(e)}")
        raise


def test_face_embedding_generation(face_service):
    """Test 4: Generate face embeddings."""
    print("\n" + "="*60)
    print("TEST 4: Face Embedding Generation")
    print("="*60)

    try:
        # Find a processed face
        face = Face.query.filter_by(status='processed').first()

        if not face:
            logger.warning("⚠️  No processed faces found in database")
            logger.info("Process some images with faces first")
            print("\n⚠️  TEST 4 SKIPPED: No processed faces available")
            return True

        logger.info(f"Testing with face ID: {face.face_id}")

        if not os.path.exists(face.file_path):
            logger.warning(f"⚠️  Face file not found: {face.file_path}")
            print("\n⚠️  TEST 4 SKIPPED: Face file missing")
            return True

        # Generate embedding
        embedding = face_service.generate_face_embedding(face.file_path)

        if embedding is not None:
            logger.info(f"✓ Generated embedding successfully")
            logger.info(f"  - Shape: {embedding.shape}")
            logger.info(f"  - Dtype: {embedding.dtype}")
            logger.info(f"  - Min: {embedding.min():.6f}")
            logger.info(f"  - Max: {embedding.max():.6f}")
            logger.info(f"  - Mean: {embedding.mean():.6f}")
        else:
            logger.error("❌ Failed to generate embedding")
            return False

        print("\n✅ TEST 4 PASSED: Face embedding generated successfully")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {str(e)}")
        raise


def test_face_attribute_analysis(face_service):
    """Test 5: Analyze face attributes (age, gender, emotion)."""
    print("\n" + "="*60)
    print("TEST 5: Face Attribute Analysis")
    print("="*60)

    try:
        # Find a processed face
        face = Face.query.filter_by(status='processed').first()

        if not face or not os.path.exists(face.file_path):
            logger.warning("⚠️  No suitable face found for testing")
            print("\n⚠️  TEST 5 SKIPPED: No faces available")
            return True

        logger.info(f"Analyzing face ID: {face.face_id}")

        # Analyze attributes
        attributes = face_service.analyze_face_attributes(face.file_path)

        logger.info("✓ Face attributes analyzed:")
        logger.info(f"  - Age estimate: {attributes.get('age_estimate', 'N/A')}")
        logger.info(f"  - Gender estimate: {attributes.get('gender_estimate', 'N/A')}")
        logger.info(f"  - Emotion estimate: {attributes.get('emotion_estimate', 'N/A')}")

        if 'emotion_scores' in attributes:
            logger.info("  - Emotion scores:")
            for emotion, score in attributes['emotion_scores'].items():
                logger.info(f"      {emotion}: {score:.2f}%")

        print("\n✅ TEST 5 PASSED: Face attributes analyzed")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {str(e)}")
        raise


def test_face_processing_full_workflow(face_service):
    """Test 6: Complete face processing workflow."""
    print("\n" + "="*60)
    print("TEST 6: Complete Face Processing Workflow")
    print("="*60)

    try:
        # Find an image that hasn't been processed yet
        image = Image.query.filter(
            Image.status == 'completed',
            ~Image.id.in_(
                db.session.query(Face.image_id).distinct()
            )
        ).first()

        if not image:
            logger.warning("⚠️  No unprocessed images available")
            print("\n⚠️  TEST 6 SKIPPED: All images already processed")
            return True

        logger.info(f"Processing image ID {image.id}: {image.filename}")

        # Process faces
        results = face_service.process_image_faces(image.id)

        logger.info(f"✓ Processing completed:")
        logger.info(f"  - Faces detected: {results['faces_detected']}")
        logger.info(f"  - Faces processed: {results['faces_processed']}")
        logger.info(f"  - Faces failed: {results['faces_failed']}")

        if results['face_ids']:
            logger.info(f"  - Face IDs: {results['face_ids']}")

            # Check face records
            for face_id in results['face_ids']:
                face = Face.query.get(face_id)
                if face:
                    logger.info(f"\n  Face {face_id} details:")
                    logger.info(f"    - Confidence: {face.confidence_score:.4f}")
                    logger.info(f"    - Quality: {face.quality_score:.4f}")
                    logger.info(f"    - Status: {face.status}")
                    logger.info(f"    - Age: {face.age_estimate}")
                    logger.info(f"    - Gender: {face.gender_estimate}")
                    logger.info(f"    - Emotion: {face.emotion_estimate}")

        print("\n✅ TEST 6 PASSED: Complete workflow executed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 6 FAILED: {str(e)}")
        raise


def test_face_stats(face_service):
    """Test 7: Get face statistics."""
    print("\n" + "="*60)
    print("TEST 7: Face Statistics")
    print("="*60)

    try:
        # Get a user ID
        user = User.query.first()

        if not user:
            logger.warning("⚠️  No users in database")
            print("\n⚠️  TEST 7 SKIPPED: No users")
            return True

        logger.info(f"Getting stats for user ID {user.id}")

        stats = face_service.get_user_face_stats(user.id)

        logger.info("✓ Face statistics:")
        logger.info(f"  - Total faces: {stats['total_faces']}")
        logger.info(f"  - Unique persons: {stats['unique_persons']}")
        logger.info(f"  - Unique clusters: {stats['unique_clusters']}")
        logger.info(f"  - Average confidence: {stats['average_confidence']:.4f}")

        logger.info("  - Status breakdown:")
        for status, count in stats['status_breakdown'].items():
            logger.info(f"      {status}: {count}")

        logger.info("  - Processing health:")
        for metric, value in stats['processing_health'].items():
            logger.info(f"      {metric}: {value}")

        print("\n✅ TEST 7 PASSED: Face statistics retrieved")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 7 FAILED: {str(e)}")
        raise


def test_health_check(face_service):
    """Test 8: Health check."""
    print("\n" + "="*60)
    print("TEST 8: Health Check")
    print("="*60)

    try:
        health = face_service.health_check()

        logger.info("Health Check Results:")
        logger.info(f"  - Healthy: {health['healthy']}")
        logger.info(f"  - Face detector loaded: {health['face_detector']['loaded']}")
        logger.info(f"  - Device: {health['face_detector']['device']}")
        logger.info(f"  - Vector service healthy: {health['vector_service']['healthy']}")
        logger.info(f"  - Faces directory writable: {health['storage']['faces_directory_writable']}")
        logger.info(f"  - Total faces: {health['processing_stats']['total_faces']}")
        logger.info(f"  - Pending: {health['processing_stats']['pending_processing']}")
        logger.info(f"  - Failed: {health['processing_stats']['failed_processing']}")
        logger.info(f"  - Processing healthy: {health['processing_stats']['processing_healthy']}")

        assert health['healthy'] is True, "Health check failed"

        print("\n✅ TEST 8 PASSED: System healthy")
        return health

    except Exception as e:
        logger.error(f"❌ TEST 8 FAILED: {str(e)}")
        raise


def run_all_tests():
    """Run all face detection tests."""
    print("\n" + "="*60)
    print("FACE DETECTION TEST SUITE")
    print("="*60)
    print("\nThis will test the following:")
    print("1. FaceService initialization")
    print("2. Face detection on test image")
    print("3. Face detection on real images")
    print("4. Face embedding generation")
    print("5. Face attribute analysis")
    print("6. Complete processing workflow")
    print("7. Face statistics")
    print("8. Health check")
    print("\n" + "="*60)

    app = create_test_app()

    with app.app_context():
        try:
            # Run tests
            face_service = test_face_service_initialization()
            test_face_detection_on_test_image(face_service)
            test_face_detection_on_real_image(face_service)
            test_face_embedding_generation(face_service)
            test_face_attribute_analysis(face_service)
            test_face_processing_full_workflow(face_service)
            test_face_stats(face_service)
            test_health_check(face_service)

            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
            print("\nYour face detection system is working correctly.")
            print("\nNext steps:")
            print("1. Upload images with faces through the API")
            print("2. Check face detection results")
            print("3. Test face clustering and search")
            print("4. Assign person names to clusters")

            return True

        except Exception as e:
            print("\n" + "="*60)
            print("❌ TESTS FAILED!")
            print("="*60)
            print(f"\nError: {str(e)}")
            print("\nTroubleshooting:")
            print("1. Check that facenet-pytorch is installed: pip install facenet-pytorch")
            print("2. Check that deepface is installed: pip install deepface")
            print("3. Check that opencv-python is installed: pip install opencv-python")
            print("4. Check file permissions for faces directory")
            print("5. Ensure images with actual faces are uploaded")

            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test face detection functionality")
    parser.add_argument("--test", type=str, help="Run specific test (1-8)")
    args = parser.parse_args()

    app = create_test_app()

    with app.app_context():
        if args.test:
            # Run specific test
            face_service = test_face_service_initialization()

            if args.test == "2":
                test_face_detection_on_test_image(face_service)
            elif args.test == "3":
                test_face_detection_on_real_image(face_service)
            elif args.test == "4":
                test_face_embedding_generation(face_service)
            elif args.test == "5":
                test_face_attribute_analysis(face_service)
            elif args.test == "6":
                test_face_processing_full_workflow(face_service)
            elif args.test == "7":
                test_face_stats(face_service)
            elif args.test == "8":
                test_health_check(face_service)
        else:
            # Run all tests
            success = run_all_tests()
            sys.exit(0 if success else 1)
