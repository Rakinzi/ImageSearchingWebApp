import os
import hashlib
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import TAGS
import exifread
from geopy.geocoders import Nominatim
import json

def generate_thumbnail(image_data, size=(128, 128), quality=85):
    try:
        with Image.open(BytesIO(image_data)) as img:
            img = ImageOps.exif_transpose(img)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
    
    except Exception as e:
        raise Exception(f"Failed to generate thumbnail: {str(e)}")

def calculate_file_hash(file_data, algorithm='sha256'):
    hash_obj = hashlib.new(algorithm)
    if isinstance(file_data, bytes):
        hash_obj.update(file_data)
    else:
        for chunk in iter(lambda: file_data.read(4096), b""):
            hash_obj.update(chunk)
        file_data.seek(0)
    
    return hash_obj.hexdigest()

def extract_exif_data(image_data):
    try:
        exif_data = {}
        
        image_stream = BytesIO(image_data)
        tags = exifread.process_file(image_stream, details=False)
        
        crucial_tags = [
            'EXIF ImageWidth',
            'EXIF ImageLength', 
            'Image Make',
            'Image Model',
            'EXIF DateTimeOriginal',
            'EXIF DateTimeDigitized',
            'Image DateTime',
            'GPS GPSLatitude',
            'GPS GPSLatitudeRef',
            'GPS GPSLongitude',
            'GPS GPSLongitudeRef',
            'EXIF FocalLength',
            'EXIF FNumber',
            'EXIF ExposureTime',
            'EXIF ISOSpeedRatings',
            'EXIF Flash',
            'Image Orientation'
        ]
        
        for tag_name in crucial_tags:
            if tag_name in tags:
                exif_data[tag_name] = str(tags[tag_name])
        
        with Image.open(BytesIO(image_data)) as img:
            if hasattr(img, '_getexif') and img._getexif():
                exif_dict = img._getexif()
                for tag_id, value in exif_dict.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name not in ['MakerNote', 'UserComment', 'ComponentsConfiguration']:
                        try:
                            exif_data[f'PIL_{tag_name}'] = str(value)
                        except:
                            continue
        
        return exif_data
    
    except Exception as e:
        return {}

def extract_gps_coordinates(exif_data):
    try:
        lat_ref = exif_data.get('GPS GPSLatitudeRef')
        lat = exif_data.get('GPS GPSLatitude')
        lng_ref = exif_data.get('GPS GPSLongitudeRef')
        lng = exif_data.get('GPS GPSLongitude')
        
        if not all([lat_ref, lat, lng_ref, lng]):
            return None, None
        
        def convert_to_degrees(value):
            parts = str(value).replace('[', '').replace(']', '').split(',')
            if len(parts) >= 3:
                degrees = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return degrees + minutes/60.0 + seconds/3600.0
            return float(parts[0]) if parts else 0.0
        
        latitude = convert_to_degrees(lat)
        longitude = convert_to_degrees(lng)
        
        if lat_ref.strip().upper() == 'S':
            latitude = -latitude
        if lng_ref.strip().upper() == 'W':
            longitude = -longitude
        
        return latitude, longitude
    
    except Exception as e:
        return None, None

def reverse_geocode(latitude, longitude):
    try:
        geolocator = Nominatim(user_agent="ImageSearchApp/1.0")
        location = geolocator.reverse(f"{latitude}, {longitude}", timeout=10)
        
        if location:
            return {
                'address': location.address,
                'city': location.raw.get('address', {}).get('city'),
                'country': location.raw.get('address', {}).get('country'),
                'country_code': location.raw.get('address', {}).get('country_code'),
                'state': location.raw.get('address', {}).get('state'),
                'postcode': location.raw.get('address', {}).get('postcode')
            }
    except Exception as e:
        pass
    
    return None

def extract_date_from_exif(exif_data):
    date_fields = [
        'EXIF DateTimeOriginal',
        'EXIF DateTimeDigitized', 
        'Image DateTime',
        'PIL_DateTimeOriginal',
        'PIL_DateTimeDigitized',
        'PIL_DateTime'
    ]
    
    for field in date_fields:
        if field in exif_data:
            try:
                date_str = exif_data[field].strip()
                if ':' in date_str and ' ' in date_str:
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                elif ':' in date_str:
                    return datetime.strptime(date_str, '%Y:%m:%d')
            except ValueError:
                continue
    
    return None

def get_image_dimensions(image_data):
    try:
        with Image.open(BytesIO(image_data)) as img:
            return img.size
    except Exception:
        return None, None

def optimize_image_for_processing(image_data, max_dimension=1024):
    try:
        with Image.open(BytesIO(image_data)) as img:
            img = ImageOps.exif_transpose(img)
            
            width, height = img.size
            if max(width, height) > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * max_dimension / width)
                else:
                    new_height = max_dimension
                    new_width = int(width * max_dimension / height)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            if img.mode != 'RGB':
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                else:
                    img = img.convert('RGB')
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            
            return output.getvalue()
    
    except Exception as e:
        return image_data

def generate_unique_id(prefix=''):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = uuid.uuid4().hex[:8]
    return f"{prefix}{timestamp}_{random_suffix}"

def safe_filename(filename, max_length=255):
    import re
    
    if not filename:
        return generate_unique_id('file_')
    
    name, ext = os.path.splitext(filename)
    
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    name = name.strip('-')
    
    if not name:
        name = generate_unique_id('file_')
    
    safe_name = f"{name}{ext.lower()}"
    
    if len(safe_name) > max_length:
        available_length = max_length - len(ext)
        name = name[:available_length]
        safe_name = f"{name}{ext.lower()}"
    
    return safe_name

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def create_directory_structure(base_path, user_id=None):
    paths = {
        'images': os.path.join(base_path, 'images'),
        'thumbnails': os.path.join(base_path, 'thumbnails'),
        'faces': os.path.join(base_path, 'faces')
    }
    
    if user_id:
        for key in paths:
            paths[key] = os.path.join(paths[key], str(user_id))
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    return paths

def validate_and_process_image(file_data, filename=None):
    if not file_data:
        raise ValueError("No file data provided")
    
    try:
        with Image.open(BytesIO(file_data)) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")
    
    file_size = len(file_data)
    checksum = calculate_file_hash(file_data)
    exif_data = extract_exif_data(file_data)
    
    latitude, longitude = extract_gps_coordinates(exif_data)
    location_data = None
    if latitude and longitude:
        location_data = reverse_geocode(latitude, longitude)
    
    image_date = extract_date_from_exif(exif_data)
    
    thumbnail_data = generate_thumbnail(file_data)
    optimized_data = optimize_image_for_processing(file_data)
    
    return {
        'original_data': file_data,
        'thumbnail_data': thumbnail_data,
        'optimized_data': optimized_data,
        'width': width,
        'height': height,
        'format': format_name,
        'mode': mode,
        'file_size': file_size,
        'checksum': checksum,
        'exif_data': exif_data,
        'image_date': image_date,
        'latitude': latitude,
        'longitude': longitude,
        'location_data': location_data,
        'filename': safe_filename(filename) if filename else generate_unique_id('image_') + '.jpg'
    }

def batch_process_images(image_list, batch_size=10):
    results = []
    errors = []
    
    for i in range(0, len(image_list), batch_size):
        batch = image_list[i:i + batch_size]
        batch_results = []
        
        for image_data in batch:
            try:
                result = validate_and_process_image(image_data['data'], image_data.get('filename'))
                batch_results.append(result)
            except Exception as e:
                errors.append({
                    'filename': image_data.get('filename', 'unknown'),
                    'error': str(e)
                })
        
        results.extend(batch_results)
    
    return results, errors

def create_image_metadata(processed_data, user_id):
    return {
        'user_id': user_id,
        'filename': processed_data['filename'],
        'original_filename': processed_data.get('original_filename', processed_data['filename']),
        'file_size': processed_data['file_size'],
        'checksum': processed_data['checksum'],
        'width': processed_data['width'],
        'height': processed_data['height'],
        'format': processed_data['format'],
        'exif_data': processed_data['exif_data'],
        'image_date': processed_data['image_date'],
        'location_data': processed_data['location_data'],
        'latitude': processed_data['latitude'],
        'longitude': processed_data['longitude'],
        'processing_status': 'pending',
        'created_at': datetime.utcnow()
    }