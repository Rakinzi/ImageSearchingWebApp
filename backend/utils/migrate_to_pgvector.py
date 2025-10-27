"""
Migration script to transfer vectors from ChromaDB to pgvector.

This script:
1. Regenerates embeddings for all images using the new ViT-L/14 model
2. Stores embeddings directly in PostgreSQL using pgvector
3. Tracks progress and handles errors gracefully

Usage:
    python utils/migrate_to_pgvector.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.modern_image import ModernImage, ImageStatus
from services.vector_service import VectorService
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_embeddings():
    """
    Migrate all image embeddings to pgvector using new ViT-L/14 model.

    This function regenerates embeddings for better accuracy rather than
    just transferring old ones.
    """
    app = create_app()

    with app.app_context():
        logger.info("=" * 80)
        logger.info("Starting migration to pgvector with OpenCLIP ViT-L/14")
        logger.info("=" * 80)

        # Initialize vector service with new model
        logger.info("Initializing OpenCLIP ViT-L/14 model...")
        vector_service = VectorService()

        # Get all completed images without pgvector embeddings
        images = ModernImage.query.filter(
            ModernImage.status == ImageStatus.COMPLETED,
            ModernImage.embedding.is_(None)
        ).all()

        total_images = len(images)
        logger.info(f"Found {total_images} images to migrate")

        if total_images == 0:
            logger.info("No images to migrate. All done!")
            return

        successful = 0
        failed = 0
        skipped = 0

        for idx, image in enumerate(images, 1):
            try:
                logger.info(f"\n[{idx}/{total_images}] Processing image {image.id}: {image.filename}")

                # Check if image file exists
                upload_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
                full_path = os.path.join(upload_dir, image.file_path)

                if not os.path.exists(full_path):
                    logger.warning(f"⚠️  Image file not found: {full_path}")
                    skipped += 1
                    continue

                # Read image file
                with open(full_path, 'rb') as f:
                    image_data = f.read()

                # Generate new embedding with ViT-L/14
                logger.info(f"   Generating 768-dim embedding with ViT-L/14...")
                embedding = vector_service.generate_image_embedding(image_data)

                # Store in database
                logger.info(f"   Storing embedding in pgvector...")
                success = vector_service.store_embedding_to_db(image.id, embedding)

                if success:
                    successful += 1
                    logger.info(f"   ✅ Successfully migrated image {image.id}")
                else:
                    failed += 1
                    logger.error(f"   ❌ Failed to store embedding for image {image.id}")

                # Progress update every 10 images
                if idx % 10 == 0:
                    logger.info(f"\n📊 Progress: {idx}/{total_images} ({successful} successful, {failed} failed, {skipped} skipped)")

            except Exception as e:
                failed += 1
                logger.error(f"   ❌ Error processing image {image.id}: {str(e)}")
                continue

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("Migration Complete!")
        logger.info("=" * 80)
        logger.info(f"Total images processed: {total_images}")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⚠️  Skipped: {skipped}")
        logger.info(f"Success rate: {(successful/total_images*100):.1f}%")
        logger.info("=" * 80)


def verify_migration():
    """Verify that embeddings were migrated correctly."""
    app = create_app()

    with app.app_context():
        logger.info("\n" + "=" * 80)
        logger.info("Verifying Migration")
        logger.info("=" * 80)

        # Count images with embeddings
        total_images = ModernImage.query.filter(
            ModernImage.status == ImageStatus.COMPLETED
        ).count()

        images_with_embeddings = ModernImage.query.filter(
            ModernImage.status == ImageStatus.COMPLETED,
            ModernImage.embedding.isnot(None)
        ).count()

        images_with_vit_l14 = ModernImage.query.filter(
            ModernImage.status == ImageStatus.COMPLETED,
            ModernImage.embedding.isnot(None),
            ModernImage.embedding_model == 'ViT-L-14'
        ).count()

        logger.info(f"Total completed images: {total_images}")
        logger.info(f"Images with pgvector embeddings: {images_with_embeddings}")
        logger.info(f"Images with ViT-L/14 embeddings: {images_with_vit_l14}")

        if total_images > 0:
            coverage = (images_with_embeddings / total_images) * 100
            logger.info(f"Coverage: {coverage:.1f}%")

            if coverage >= 99:
                logger.info("✅ Migration verification PASSED")
            else:
                logger.warning("⚠️  Some images missing embeddings")

        logger.info("=" * 80)


def test_search():
    """Test pgvector search functionality."""
    app = create_app()

    with app.app_context():
        logger.info("\n" + "=" * 80)
        logger.info("Testing pgvector Search")
        logger.info("=" * 80)

        vector_service = VectorService()

        # Test query
        test_query = "beautiful sunset"
        logger.info(f"Test query: '{test_query}'")

        try:
            results = vector_service.text_to_image_search_pgvector(
                test_query,
                limit=5,
                similarity_threshold=0.3
            )

            logger.info(f"\nFound {len(results)} results:")
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. {result['metadata']['filename']} (similarity: {result['similarity']:.3f})")

            if results:
                logger.info("✅ Search test PASSED")
            else:
                logger.warning("⚠️  No results found (may be normal if no matching images)")

        except Exception as e:
            logger.error(f"❌ Search test FAILED: {str(e)}")

        logger.info("=" * 80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate vectors to pgvector')
    parser.add_argument('--verify', action='store_true', help='Verify migration status')
    parser.add_argument('--test', action='store_true', help='Test search functionality')
    parser.add_argument('--migrate', action='store_true', help='Run migration')

    args = parser.parse_args()

    if args.verify:
        verify_migration()
    elif args.test:
        test_search()
    elif args.migrate:
        migrate_embeddings()
    else:
        # Default: run migration
        print("\nThis will migrate all images to pgvector with new ViT-L/14 embeddings.")
        print("This process may take some time depending on the number of images.")
        response = input("\nContinue? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            migrate_embeddings()
            verify_migration()
            test_search()
        else:
            print("Migration cancelled.")
