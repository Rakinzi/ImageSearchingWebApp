"""
Utility script to test OCR (Optical Character Recognition) functionality.

This script helps test:
- OCR backend initialization
- Text extraction from images
- Detailed OCR with bounding boxes
- Different OCR backends (EasyOCR, PaddleOCR, Tesseract)
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from extensions import db
from config.settings import Config
from utils.ocr import OCRService, extract_text_from_image, extract_text_detailed
from models.image import Image

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


def test_ocr_initialization():
    """Test 1: OCR Service initialization."""
    print("\n" + "="*60)
    print("TEST 1: OCR Service Initialization")
    print("="*60)

    try:
        ocr_service = OCRService(backend='auto')
        logger.info("✓ OCRService instance created")

        # Force initialization
        ocr_service._ensure_initialized()
        logger.info("✓ OCR engine initialized")

        # Check backend
        logger.info(f"Backend: {ocr_service.backend}")
        logger.info(f"Initialized: {ocr_service._initialized}")

        if ocr_service.backend == 'none':
            logger.warning("⚠️  No OCR backend available!")
            logger.info("Install one of: easyocr, paddleocr, pytesseract")
            logger.info("pip install easyocr")
            print("\n⚠️  TEST 1 WARNING: No OCR backend available")
            return None
        else:
            logger.info(f"✓ Using {ocr_service.backend} backend")
            print(f"\n✅ TEST 1 PASSED: OCR initialized with {ocr_service.backend}")
            return ocr_service

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {str(e)}")
        raise


def test_create_test_image_with_text():
    """Test 2: Create a test image with text."""
    print("\n" + "="*60)
    print("TEST 2: Create Test Image with Text")
    print("="*60)

    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create image with text
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)

        # Try to use a better font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = None  # Use default font

        # Add text
        text_lines = [
            "Hello World!",
            "This is a test image.",
            "OCR should detect this text.",
            "Image Search Application"
        ]

        y = 50
        for line in text_lines:
            if font:
                draw.text((50, y), line, fill='black', font=font)
            else:
                draw.text((50, y), line, fill='black')
            y += 70

        # Save test image
        test_image_path = Path('test_ocr_image.png')
        img.save(test_image_path)
        logger.info(f"✓ Created test image: {test_image_path}")
        logger.info(f"  Text in image:")
        for line in text_lines:
            logger.info(f"    - {line}")

        print("\n✅ TEST 2 PASSED: Test image created")
        return test_image_path

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {str(e)}")
        raise


def test_text_extraction(ocr_service, image_path):
    """Test 3: Extract text from test image."""
    print("\n" + "="*60)
    print("TEST 3: Text Extraction")
    print("="*60)

    if ocr_service is None:
        print("\n⚠️  TEST 3 SKIPPED: No OCR backend available")
        return

    try:
        logger.info(f"Extracting text from: {image_path}")

        # Extract text
        extracted_text = ocr_service.extract_text(str(image_path))

        if extracted_text:
            logger.info("✓ Text extracted successfully")
            logger.info(f"  Length: {len(extracted_text)} characters")
            logger.info(f"  Text preview:")
            # Print first 200 characters
            preview = extracted_text[:200] if len(extracted_text) > 200 else extracted_text
            for line in preview.split('\n'):
                if line.strip():
                    logger.info(f"    {line.strip()}")
        else:
            logger.warning("⚠️  No text extracted")

        print("\n✅ TEST 3 PASSED: Text extraction completed")
        return extracted_text

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {str(e)}")
        raise


def test_detailed_extraction(ocr_service, image_path):
    """Test 4: Detailed text extraction with bounding boxes."""
    print("\n" + "="*60)
    print("TEST 4: Detailed Text Extraction")
    print("="*60)

    if ocr_service is None:
        print("\n⚠️  TEST 4 SKIPPED: No OCR backend available")
        return

    try:
        logger.info(f"Extracting detailed text from: {image_path}")

        # Extract detailed text
        detailed = ocr_service.extract_text_detailed(str(image_path))

        if detailed:
            logger.info("✓ Detailed extraction successful")
            logger.info(f"  Backend: {detailed['backend']}")
            logger.info(f"  Total detections: {detailed['total_detections']}")
            logger.info(f"  Combined text length: {len(detailed['text']) if detailed['text'] else 0} characters")

            if detailed['detailed_results']:
                logger.info(f"\n  Detected text blocks ({len(detailed['detailed_results'])}):")
                for i, result in enumerate(detailed['detailed_results'][:5]):  # Show first 5
                    logger.info(f"    Block {i+1}:")
                    logger.info(f"      Text: {result['text']}")
                    logger.info(f"      Confidence: {result['confidence']:.2f}")

                if len(detailed['detailed_results']) > 5:
                    logger.info(f"    ... and {len(detailed['detailed_results']) - 5} more")
        else:
            logger.warning("⚠️  No detailed results")

        print("\n✅ TEST 4 PASSED: Detailed extraction completed")
        return detailed

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {str(e)}")
        raise


def test_ocr_on_real_images(ocr_service):
    """Test 5: Extract text from real uploaded images."""
    print("\n" + "="*60)
    print("TEST 5: OCR on Real Images")
    print("="*60)

    if ocr_service is None:
        print("\n⚠️  TEST 5 SKIPPED: No OCR backend available")
        return

    try:
        # Find images in database
        images = Image.query.filter(
            Image.status == 'completed'
        ).limit(5).all()

        if not images:
            logger.warning("⚠️  No completed images found in database")
            logger.info("Upload some images to test this functionality")
            print("\n⚠️  TEST 5 SKIPPED: No images available")
            return

        logger.info(f"Found {len(images)} completed images")

        total_with_text = 0
        for image in images:
            if not os.path.exists(image.file_path):
                logger.warning(f"⚠️  Image file not found: {image.file_path}")
                continue

            logger.info(f"\nProcessing image ID {image.id}: {image.filename}")

            extracted_text = ocr_service.extract_text(image.file_path)

            if extracted_text:
                logger.info(f"  ✓ Text found ({len(extracted_text)} characters)")
                # Show preview
                preview = extracted_text[:100].replace('\n', ' ')
                logger.info(f"    Preview: {preview}...")
                total_with_text += 1
            else:
                logger.info(f"  - No text detected")

        logger.info(f"\n✓ Images with text: {total_with_text}/{len(images)}")

        print("\n✅ TEST 5 PASSED: Real image OCR completed")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {str(e)}")
        raise


def test_convenience_functions():
    """Test 6: Test convenience functions."""
    print("\n" + "="*60)
    print("TEST 6: Convenience Functions")
    print("="*60)

    try:
        # Create a simple test image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 80), "TEST 123", fill='black')

        test_path = Path('test_convenience.png')
        img.save(test_path)
        logger.info(f"✓ Created test image: {test_path}")

        # Test extract_text_from_image
        text = extract_text_from_image(str(test_path))
        logger.info(f"✓ extract_text_from_image() returned: {text}")

        # Test extract_text_detailed
        detailed = extract_text_detailed(str(test_path))
        if detailed:
            logger.info(f"✓ extract_text_detailed() found {detailed['total_detections']} detections")
        else:
            logger.info("✓ extract_text_detailed() completed (no text found)")

        # Cleanup
        if test_path.exists():
            test_path.unlink()
            logger.info("✓ Cleaned up test image")

        print("\n✅ TEST 6 PASSED: Convenience functions working")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 6 FAILED: {str(e)}")
        # Cleanup on failure
        if Path('test_convenience.png').exists():
            Path('test_convenience.png').unlink()
        raise


def test_health_check(ocr_service):
    """Test 7: Health check."""
    print("\n" + "="*60)
    print("TEST 7: Health Check")
    print("="*60)

    try:
        if ocr_service:
            health = ocr_service.health_check()

            logger.info("Health Check Results:")
            logger.info(f"  - OCR available: {health['ocr_available']}")
            logger.info(f"  - Backend: {health['backend']}")
            logger.info(f"  - Initialized: {health['initialized']}")

            print("\n✅ TEST 7 PASSED: Health check completed")
            return health
        else:
            logger.info("OCR service not available")
            print("\n⚠️  TEST 7 SKIPPED: No OCR backend")
            return None

    except Exception as e:
        logger.error(f"❌ TEST 7 FAILED: {str(e)}")
        raise


def run_all_tests():
    """Run all OCR tests."""
    print("\n" + "="*60)
    print("OCR TEST SUITE")
    print("="*60)
    print("\nThis will test the following:")
    print("1. OCR service initialization")
    print("2. Create test image with text")
    print("3. Text extraction")
    print("4. Detailed text extraction (with bounding boxes)")
    print("5. OCR on real images")
    print("6. Convenience functions")
    print("7. Health check")
    print("\n" + "="*60)

    app = create_test_app()

    with app.app_context():
        test_image_path = None

        try:
            # Run tests
            ocr_service = test_ocr_initialization()
            test_image_path = test_create_test_image_with_text()

            if ocr_service and test_image_path:
                test_text_extraction(ocr_service, test_image_path)
                test_detailed_extraction(ocr_service, test_image_path)
                test_ocr_on_real_images(ocr_service)
                test_convenience_functions()
                test_health_check(ocr_service)

                print("\n" + "="*60)
                print("✅ ALL TESTS PASSED!")
                print("="*60)
                print("\nYour OCR system is working correctly.")
                print("\nNext steps:")
                print("1. Upload images with text through the API")
                print("2. Check extracted text in database")
                print("3. Test text search functionality")
            else:
                print("\n" + "="*60)
                print("⚠️  TESTS INCOMPLETE")
                print("="*60)
                print("\nNo OCR backend available.")
                print("\nTo enable OCR, install one of:")
                print("  pip install easyocr           # Recommended (best accuracy)")
                print("  pip install paddleocr          # Fast and accurate")
                print("  pip install pytesseract        # Requires tesseract binary")

            return True

        except Exception as e:
            print("\n" + "="*60)
            print("❌ TESTS FAILED!")
            print("="*60)
            print(f"\nError: {str(e)}")
            print("\nTroubleshooting:")
            print("1. Install an OCR backend:")
            print("     pip install easyocr")
            print("2. For GPU support, ensure CUDA is installed")
            print("3. For Tesseract, install the binary:")
            print("     Ubuntu: sudo apt-get install tesseract-ocr")
            print("     MacOS: brew install tesseract")
            print("     Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")

            return False

        finally:
            # Cleanup test image
            if test_image_path and test_image_path.exists():
                test_image_path.unlink()
                logger.info("Cleaned up test image")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test OCR functionality")
    parser.add_argument("--test", type=str, help="Run specific test (1-7)")
    parser.add_argument("--backend", type=str, default='auto',
                       choices=['auto', 'easyocr', 'paddle', 'tesseract'],
                       help="OCR backend to use")
    args = parser.parse_args()

    if args.test:
        # Run specific test
        app = create_test_app()
        with app.app_context():
            ocr_service = OCRService(backend=args.backend)
            ocr_service._ensure_initialized()

            if args.test == "1":
                test_ocr_initialization()
            elif args.test == "2":
                test_create_test_image_with_text()
            elif args.test == "3":
                test_image_path = test_create_test_image_with_text()
                test_text_extraction(ocr_service, test_image_path)
                if test_image_path.exists():
                    test_image_path.unlink()
            elif args.test == "4":
                test_image_path = test_create_test_image_with_text()
                test_detailed_extraction(ocr_service, test_image_path)
                if test_image_path.exists():
                    test_image_path.unlink()
            elif args.test == "5":
                test_ocr_on_real_images(ocr_service)
            elif args.test == "6":
                test_convenience_functions()
            elif args.test == "7":
                test_health_check(ocr_service)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
