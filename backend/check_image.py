#!/usr/bin/env python3
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.modern_image import ModernImage

app = create_app()

with app.app_context():
    # Check image 15
    img = ModernImage.query.get(15)

    if img:
        print(f"Image ID: {img.id}")
        print(f"Status: {img.status.value}")
        print(f"Thumbnail path: {repr(img.thumbnail_path)}")
        print(f"File path: {repr(img.file_path)}")
        print(f"User ID: {img.user_id}")
    else:
        print("Image with ID 15 not found")

    print("\n" + "="*50)
    print("Images without thumbnails:")
    print("="*50)

    imgs = ModernImage.query.filter(
        (ModernImage.thumbnail_path.is_(None)) | (ModernImage.thumbnail_path == '')
    ).all()

    for img in imgs:
        print(f"ID {img.id}: status={img.status.value}, filename={img.filename}")
