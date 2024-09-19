import firebase_admin
from firebase_admin import credentials, storage

# Your Firebase configuration file
firebase_config_file = 'path/to/your/serviceAccountKey.json'

cred = credentials.Certificate(firebase_config_file)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'g-drive-one.appspot.com'  # Replace with your Firebase storage bucket
})

bucket = storage.bucket()

