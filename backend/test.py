import base64

# Original string
original_string = "Hello, World!"

# Encode to URL-safe Base64
url_safe_encoded = base64.urlsafe_b64encode(original_string.encode()).decode()
print("URL Safe Base64 Encoded:", url_safe_encoded)

# Decode from URL-safe Base64
url_safe_decoded = base64.urlsafe_b64decode(url_safe_encoded.encode()).decode()
print("URL Safe Base64 Decoded:", url_safe_decoded)
