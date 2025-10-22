import re
import os
from email_validator import validate_email as email_validate, EmailNotValidError
from werkzeug.datastructures import FileStorage
from PIL import Image
import magic

def validate_email(email):
    try:
        validation = email_validate(email)
        return True, validation.email
    except EmailNotValidError as e:
        return False, str(e)

def validate_password(password):
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 128:
        errors.append("Password must be less than 128 characters long")

    return len(errors) == 0, errors

def validate_name(name):
    if not name or not isinstance(name, str):
        return False, "Name is required"
    
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters long"
    
    if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
        return False, "Name contains invalid characters"
    
    return True, name

def validate_image_file(file):
    if not isinstance(file, FileStorage):
        return False, "Invalid file object"
    
    if not file.filename:
        return False, "No filename provided"
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    max_size = 16 * 1024 * 1024  # 16MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        return False, f"File size ({file_size} bytes) exceeds maximum allowed size (16MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    try:
        file_data = file.read()
        file.seek(0)
        
        mime_type = magic.from_buffer(file_data, mime=True)
        allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 
            'image/webp', 'image/bmp'
        }
        
        if mime_type not in allowed_mime_types:
            return False, f"Invalid file type detected: {mime_type}"
        
        try:
            with Image.open(file) as img:
                img.verify()
            file.seek(0)
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
        
    except Exception as e:
        return False, f"Error validating file: {str(e)}"
    
    return True, "Valid image file"

def validate_search_query(query):
    if not query or not isinstance(query, str):
        return False, "Search query is required"
    
    query = query.strip()
    if len(query) < 1:
        return False, "Search query cannot be empty"
    
    if len(query) > 200:
        return False, "Search query is too long (maximum 200 characters)"
    
    forbidden_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.(cookie|write)',
        r'window\.(location|open)'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Search query contains invalid characters"
    
    return True, query

def validate_coordinates(lat, lng):
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"
    
    if not (-90 <= lat <= 90):
        return False, "Latitude must be between -90 and 90"
    
    if not (-180 <= lng <= 180):
        return False, "Longitude must be between -180 and 180"
    
    return True, (lat, lng)

def validate_date_range(start_date, end_date):
    from datetime import datetime
    
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        return False, "Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
    
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    max_range_days = 365
    if (end_date - start_date).days > max_range_days:
        return False, f"Date range cannot exceed {max_range_days} days"
    
    return True, (start_date, end_date)

def validate_pagination(page, per_page):
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 20
    except (ValueError, TypeError):
        return False, "Invalid pagination parameters"
    
    if page < 1:
        return False, "Page number must be positive"
    
    if per_page < 1 or per_page > 100:
        return False, "Items per page must be between 1 and 100"
    
    return True, (page, per_page)

def validate_sort_params(sort_by, sort_order, allowed_fields):
    if sort_by and sort_by not in allowed_fields:
        return False, f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}"
    
    if sort_order and sort_order.lower() not in ['asc', 'desc']:
        return False, "Sort order must be 'asc' or 'desc'"
    
    return True, (sort_by or 'created_at', sort_order or 'desc')

def validate_face_coordinates(coordinates):
    if not isinstance(coordinates, dict):
        return False, "Face coordinates must be a dictionary"
    
    required_fields = ['x1', 'y1', 'x2', 'y2']
    for field in required_fields:
        if field not in coordinates:
            return False, f"Missing required coordinate field: {field}"
        
        try:
            value = float(coordinates[field])
            if value < 0:
                return False, f"Coordinate {field} must be non-negative"
        except (ValueError, TypeError):
            return False, f"Invalid coordinate value for {field}"
    
    x1, y1, x2, y2 = coordinates['x1'], coordinates['y1'], coordinates['x2'], coordinates['y2']
    
    if x1 >= x2 or y1 >= y2:
        return False, "Invalid bounding box coordinates"
    
    return True, coordinates

def validate_confidence_score(score):
    try:
        score = float(score)
    except (ValueError, TypeError):
        return False, "Confidence score must be a number"
    
    if not (0.0 <= score <= 1.0):
        return False, "Confidence score must be between 0.0 and 1.0"
    
    return True, score

def validate_person_name(name):
    if not name or not isinstance(name, str):
        return False, "Person name is required"
    
    name = name.strip()
    if len(name) < 1:
        return False, "Person name cannot be empty"
    
    if len(name) > 100:
        return False, "Person name is too long (maximum 100 characters)"
    
    if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
        return False, "Person name contains invalid characters"
    
    return True, name

class ValidationError(Exception):
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class RequestValidator:
    @staticmethod
    def validate_json_request(data, schema):
        errors = {}
        
        for field, rules in schema.items():
            value = data.get(field)
            
            if rules.get('required', False) and (value is None or value == ''):
                errors[field] = 'This field is required'
                continue
            
            if value is not None:
                field_type = rules.get('type')
                if field_type and not isinstance(value, field_type):
                    errors[field] = f'Expected {field_type.__name__}, got {type(value).__name__}'
                    continue
                
                if 'min_length' in rules and len(str(value)) < rules['min_length']:
                    errors[field] = f'Minimum length is {rules["min_length"]}'
                
                if 'max_length' in rules and len(str(value)) > rules['max_length']:
                    errors[field] = f'Maximum length is {rules["max_length"]}'
                
                if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
                    errors[field] = 'Invalid format'
                
                if 'custom_validator' in rules:
                    is_valid, error_msg = rules['custom_validator'](value)
                    if not is_valid:
                        errors[field] = error_msg
        
        return len(errors) == 0, errors