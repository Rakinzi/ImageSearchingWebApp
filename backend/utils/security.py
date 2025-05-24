import os
import re
import hashlib
import secrets
import uuid
from urllib.parse import urlparse
from flask import request
from werkzeug.utils import secure_filename
import bleach

def setup_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        if not app.debug:
            response.headers['Server'] = 'ImageSearch/1.0'
        
        return response

def sanitize_input(input_string, max_length=1000):
    if not input_string or not isinstance(input_string, str):
        return ""
    
    input_string = input_string.strip()[:max_length]
    
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    allowed_attributes = {}
    
    cleaned = bleach.clean(
        input_string,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return cleaned

def validate_file_type(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_secure_filename(original_filename):
    if not original_filename:
        return f"{uuid.uuid4().hex}.bin"
    
    name, ext = os.path.splitext(original_filename)
    secure_name = secure_filename(name)
    
    if not secure_name:
        secure_name = uuid.uuid4().hex
    
    timestamp = secrets.token_hex(8)
    return f"{secure_name}_{timestamp}{ext.lower()}"

def calculate_file_hash(file_data, algorithm='sha256'):
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(file_data)
    return hash_obj.hexdigest()

def validate_image_signature(file_data):
    image_signatures = {
        b'\xFF\xD8\xFF': 'jpeg',
        b'\x89PNG\r\n\x1A\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'RIFF': 'webp',
        b'BM': 'bmp'
    }
    
    for signature, file_type in image_signatures.items():
        if file_data.startswith(signature):
            return True, file_type
    
    return False, None

def check_file_size(file_data, max_size_mb=16):
    max_size_bytes = max_size_mb * 1024 * 1024
    return len(file_data) <= max_size_bytes

def detect_malicious_patterns(file_data):
    suspicious_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'eval(',
        b'document.cookie',
        b'document.write'
    ]
    
    file_data_lower = file_data.lower()
    for pattern in suspicious_patterns:
        if pattern in file_data_lower:
            return True
    
    return False

def sanitize_filename_for_path(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.replace('..', '_')
    filename = filename.strip('. ')
    
    if not filename:
        filename = f"file_{uuid.uuid4().hex[:8]}"
    
    return filename

def validate_request_origin(allowed_origins=None):
    if not allowed_origins:
        return True
    
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')
    
    if origin:
        return origin in allowed_origins
    
    if referer:
        parsed_referer = urlparse(referer)
        referer_origin = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
        return referer_origin in allowed_origins
    
    return False

def generate_csrf_token():
    return secrets.token_urlsafe(32)

def validate_csrf_token(token, session_token):
    if not token or not session_token:
        return False
    return secrets.compare_digest(token, session_token)

def hash_password_secure(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(32)
    
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + key

def verify_password_secure(password, hashed_password):
    salt = hashed_password[:32]
    key = hashed_password[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return secrets.compare_digest(key, new_key)

def generate_api_key():
    return f"isk_{secrets.token_urlsafe(32)}"

def validate_api_key_format(api_key):
    if not api_key or not isinstance(api_key, str):
        return False
    return api_key.startswith('isk_') and len(api_key) == 47

def check_sql_injection_patterns(input_string):
    if not isinstance(input_string, str):
        return False
    
    sql_patterns = [
        r"('|(\\'))+.*(;|--|#)",
        r"\b(union|select|insert|update|delete|drop|create|alter)\b",
        r"(\\x[0-9a-f]{2})+",
        r"(\\u[0-9a-f]{4})+",
        r"\b(exec|execute|sp_|xp_)\b"
    ]
    
    input_lower = input_string.lower()
    for pattern in sql_patterns:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return True
    
    return False

def sanitize_search_query(query):
    if not query or not isinstance(query, str):
        return ""
    
    query = query.strip()
    
    if check_sql_injection_patterns(query):
        return ""
    
    query = re.sub(r'[<>"\';\\]', '', query)
    query = query[:200]
    
    return query

def rate_limit_key(prefix, identifier):
    return f"rate_limit:{prefix}:{hashlib.md5(str(identifier).encode()).hexdigest()}"

def is_safe_redirect_url(url, allowed_hosts=None):
    if not url:
        return False
    
    if url.startswith('//') or url.startswith('http://') or url.startswith('https://'):
        parsed = urlparse(url)
        if allowed_hosts:
            return parsed.netloc in allowed_hosts
        return False
    
    return url.startswith('/') and not url.startswith('//')

class SecurityValidator:
    @staticmethod
    def validate_file_upload(file_data, filename, allowed_types, max_size_mb=16):
        errors = []
        
        if not file_data:
            errors.append("No file data provided")
            return False, errors
        
        if not check_file_size(file_data, max_size_mb):
            errors.append(f"File size exceeds {max_size_mb}MB limit")
        
        is_valid_image, detected_type = validate_image_signature(file_data)
        if not is_valid_image:
            errors.append("Invalid image file signature")
        
        if filename and not validate_file_type(filename, allowed_types):
            errors.append("File type not allowed")
        
        if detect_malicious_patterns(file_data):
            errors.append("Potentially malicious content detected")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_user_input(data, required_fields=None, max_lengths=None):
        errors = []
        
        if required_fields:
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Required field '{field}' is missing")
        
        if max_lengths:
            for field, max_length in max_lengths.items():
                if field in data and isinstance(data[field], str):
                    if len(data[field]) > max_length:
                        errors.append(f"Field '{field}' exceeds maximum length of {max_length}")
        
        for field, value in data.items():
            if isinstance(value, str):
                if check_sql_injection_patterns(value):
                    errors.append(f"Invalid characters detected in field '{field}'")
        
        return len(errors) == 0, errors