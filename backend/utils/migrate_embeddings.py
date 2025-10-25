"""
Migration script to fix embeddings with old ID format.

This script:
1. Finds all images with old vector_id format (img_{id}_{user_id})
2. Regenerates embeddings with new format (just {id})
3. Updates the database records
"""

import os
import sys
import logging
from pathlib import Path

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


def create_app():
    """Create Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def migrate_legacy_embeddings(dry_run=True):
    """Migrate embeddings from old format to new format.

    Args:
        dry_run: If True, only report what would be changed without making changes
    """
    print("\n" + "="*60)
    print("EMBEDDINGS MIGRATION SCRIPT")
    print("="*60)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be made)'}")
    print("="*60)

    vector_service = VectorService()

    # Find all images with old vector_id format
    legacy_images = []
    modern_images = []

    # Check Image table (v1)
    all_v1_images = Image.query.filter(Image.vector_id.isnot(None)).all()
    for img in all_v1_images:
        if img.vector_id and '_' in img.vector_id:
            # Old format: img_{id}_{user_id}
            legacy_images.append(('v1', img))
        elif img.vector_id:
            modern_images.append(('v1', img))

    # Check ModernImage table (v2)
    all_v2_images = ModernImage.query.filter(ModernImage.vector_id.isnot(None)).all()
    for img in all_v2_images:
        if img.vector_id and '_' in img.vector_id:
            legacy_images.append(('v2', img))
        elif img.vector_id:
            modern_images.append(('v2', img))

    print(f"\nFound {len(legacy_images)} images with old vector_id format")
    print(f"Found {len(modern_images)} images with new vector_id format")

    if not legacy_images:
        print("\n✅ No legacy embeddings found. All embeddings are up to date!")
        return True

    # Migrate legacy embeddings
    migrated_count = 0
    failed_count = 0
    skipped_count = 0

    for version, image in legacy_images:
        try:
            old_vector_id = image.vector_id
            new_vector_id = str(image.id)

            print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {version} image ID {image.id}")
            print(f"  Old vector_id: {old_vector_id}")
            print(f"  New vector_id: {new_vector_id}")

            # Check if file exists
            if not os.path.exists(image.file_path):
                print(f"  ⚠️  SKIPPED: File not found: {image.file_path}")
                skipped_count += 1
                continue

            if not dry_run:
                # Read image file
                with open(image.file_path, 'rb') as f:
                    image_data = f.read()

                # Remove old vector
                try:
                    vector_service.remove_image_vector(old_vector_id)
                    print(f"  ✓ Removed old vector: {old_vector_id}")
                except Exception as e:
                    print(f"  ⚠️  Could not remove old vector (may not exist): {e}")

                # Generate new embedding
                try:
                    embedding = vector_service.generate_image_embedding(image_data)
                    print(f"  ✓ Generated new embedding (shape: {embedding.shape})")
                except Exception as e:
                    print(f"  ❌ FAILED to generate embedding: {e}")
                    failed_count += 1
                    continue

                # Prepare metadata
                metadata = {
                    'user_id': image.user_id,
                    'filename': image.filename,
                    'file_path': image.file_path,
                    'created_at': image.created_at.isoformat()
                }

                # Store new vector
                if vector_service.store_image_vector(new_vector_id, embedding, metadata):
                    print(f"  ✓ Stored new vector: {new_vector_id}")

                    # Update database record
                    image.vector_id = new_vector_id
                    db.session.commit()
                    print(f"  ✓ Updated database record")

                    migrated_count += 1
                else:
                    print(f"  ❌ FAILED to store new vector")
                    failed_count += 1
                    db.session.rollback()
            else:
                print(f"  ✓ Would migrate this embedding")
                migrated_count += 1

        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            failed_count += 1
            if not dry_run:
                db.session.rollback()

    # Summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total legacy embeddings found: {len(legacy_images)}")
    print(f"{'Would migrate' if dry_run else 'Migrated'}: {migrated_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped (file not found): {skipped_count}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("To perform the actual migration, run with --live flag")
    else:
        print("\n✅ Migration complete!")

    return failed_count == 0


def regenerate_all_embeddings(dry_run=True):
    """Regenerate all embeddings for all images.

    Args:
        dry_run: If True, only report what would be done
    """
    print("\n" + "="*60)
    print("REGENERATE ALL EMBEDDINGS")
    print("="*60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("="*60)

    vector_service = VectorService()

    # Get all images
    all_images = []
    for img in Image.query.all():
        all_images.append(('v1', img))
    for img in ModernImage.query.all():
        all_images.append(('v2', img))

    print(f"\nFound {len(all_images)} total images")

    regenerated_count = 0
    failed_count = 0
    skipped_count = 0

    for version, image in all_images:
        try:
            vector_id = str(image.id)

            print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {version} image ID {image.id}")

            # Check if file exists
            if not os.path.exists(image.file_path):
                print(f"  ⚠️  SKIPPED: File not found")
                skipped_count += 1
                continue

            if not dry_run:
                # Read image file
                with open(image.file_path, 'rb') as f:
                    image_data = f.read()

                # Generate embedding
                embedding = vector_service.generate_image_embedding(image_data)
                print(f"  ✓ Generated embedding (shape: {embedding.shape})")

                # Prepare metadata
                metadata = {
                    'user_id': image.user_id,
                    'filename': image.filename,
                    'file_path': image.file_path,
                    'created_at': image.created_at.isoformat()
                }

                # Store vector
                if vector_service.store_image_vector(vector_id, embedding, metadata):
                    print(f"  ✓ Stored vector")

                    # Update database record
                    image.vector_id = vector_id
                    db.session.commit()
                    print(f"  ✓ Updated database")

                    regenerated_count += 1
                else:
                    print(f"  ❌ FAILED to store vector")
                    failed_count += 1
                    db.session.rollback()
            else:
                print(f"  ✓ Would regenerate embedding")
                regenerated_count += 1

        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            failed_count += 1
            if not dry_run:
                db.session.rollback()

    # Summary
    print("\n" + "="*60)
    print("REGENERATION SUMMARY")
    print("="*60)
    print(f"Total images: {len(all_images)}")
    print(f"{'Would regenerate' if dry_run else 'Regenerated'}: {regenerated_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped: {skipped_count}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("To perform the actual regeneration, run with --live flag")
    else:
        print("\n✅ Regeneration complete!")

    return failed_count == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate or regenerate embeddings")
    parser.add_argument(
        "--action",
        choices=["migrate", "regenerate"],
        default="migrate",
        help="Action to perform (migrate or regenerate)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually perform the changes (default is dry-run)"
    )

    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        dry_run = not args.live

        if args.action == "migrate":
            success = migrate_legacy_embeddings(dry_run=dry_run)
        elif args.action == "regenerate":
            print("\n⚠️  WARNING: This will regenerate ALL embeddings!")
            print("This is a resource-intensive operation.")
            if not dry_run:
                confirm = input("Are you sure you want to continue? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Aborted.")
                    sys.exit(0)
            success = regenerate_all_embeddings(dry_run=dry_run)

        sys.exit(0 if success else 1)
