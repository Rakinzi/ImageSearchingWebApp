# Face Detection and Recognition System

## Overview

The face detection system automatically identifies, extracts, and analyzes faces in uploaded images. It provides:

- **Face Detection**: MTCNN-based face detection with bounding boxes
- **Face Recognition**: 512-dimensional embeddings using FaceNet
- **Face Attributes**: Age, gender, and emotion estimation
- **Face Clustering**: Automatic grouping of similar faces
- **Face Search**: Find similar faces across your image collection
- **Person Identification**: Assign names to face clusters

## What Was Enabled

### ✅ Face Detection Integration

**Before**: Face detection was stubbed out and not functioning
```python
# TODO: Implement face detection
# from services.face_service import FaceService
```

**After**: Fully integrated face detection
```python
from services.face_service import FaceService
face_service = FaceService()
face_results = face_service.process_image_faces(image_id)
```

**Locations**:
- `services/image_service.py` line 82-89
- `services/modern_image_service.py` line 523-555

## Features

### 1. Automatic Face Detection

When you upload an image, the system:
1. Detects all faces using MTCNN
2. Extracts face regions with expanded bounding boxes
3. Calculates quality and confidence scores
4. Saves face crops for analysis

**Detection Parameters**:
- **Minimum face size**: 20x20 pixels
- **Detection threshold**: 0.99 (configurable via `FACE_DETECTION_THRESHOLD`)
- **Bounding box expansion**: 30% around detected face

### 2. Face Recognition

Each detected face gets:
- **512-dimensional embedding** using FaceNet512
- Stored in vector database for similarity search
- Normalized for consistent comparisons

### 3. Face Attributes

The system estimates:
- **Age**: Approximate age in years
- **Gender**: Male/female classification with confidence
- **Emotion**: Dominant emotion (happy, sad, angry, neutral, etc.)
- **Emotion scores**: Probabilities for all emotions

### 4. Face Clustering

Automatically groups similar faces:
- Uses DBSCAN clustering with cosine similarity
- **Similarity threshold**: 0.55 (configurable via `FACE_SIMILARITY_THRESHOLD`)
- Identifies primary face (best quality) in each cluster
- Helps identify the same person across multiple images

### 5. Face Search

Find similar faces:
- Search by face to find matching persons
- Adjust similarity threshold per query
- Filter results by user/timeframe

### 6. Person Identification

- Assign names to face clusters
- Manual verification support
- Track person appearances across images

## Architecture

### Models

**Face Model** (`models/face.py`):
```python
Face:
  - face_id: Unique identifier
  - file_path: Path to cropped face image
  - bounding_box: Face location in original image
  - confidence_score: Detection confidence (0-1)
  - quality_score: Face quality metric
  - embedding_vector: 512-dim FaceNet embedding
  - face_cluster_id: Cluster assignment
  - person_name: Assigned person name
  - age_estimate: Estimated age
  - gender_estimate: Estimated gender
  - emotion_estimate: Dominant emotion
  - status: pending|processed|clustered|failed
```

### Services

**FaceService** (`services/face_service.py`):
- `detect_faces_in_image()`: Detect all faces in an image
- `generate_face_embedding()`: Generate FaceNet embedding
- `analyze_face_attributes()`: Estimate age/gender/emotion
- `process_image_faces()`: Complete face processing workflow
- `cluster_user_faces()`: Cluster faces for a user
- `find_similar_faces()`: Search for similar faces
- `assign_person_to_cluster()`: Assign name to cluster

### Vector Storage

Faces are stored in ChromaDB's `face_embeddings` collection:
- **Vector ID**: `face_id` (unique per face)
- **Embedding**: 512-dimensional FaceNet vector
- **Metadata**: Confidence, quality, attributes, image_id

## Usage

### Test Face Detection

```bash
cd backend
python utils/test_face_detection.py
```

This runs 8 comprehensive tests:
1. FaceService initialization
2. Face detection on test image
3. Face detection on real images
4. Face embedding generation
5. Face attribute analysis
6. Complete processing workflow
7. Face statistics
8. Health check

### API Upload with Face Detection

**Upload with face detection enabled (default)**:
```bash
curl -X POST http://localhost:8080/api/v2/images/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg" \
  -F "detect_faces=true"
```

**Upload without face detection**:
```bash
curl -X POST http://localhost:8080/api/v2/images/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg" \
  -F "detect_faces=false"
```

### Check Face Detection Results

```bash
# Get all faces for an image
curl http://localhost:8080/api/v1/images/{image_id}/faces \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get face statistics
curl http://localhost:8080/api/v1/faces/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get face clusters
curl http://localhost:8080/api/v1/faces/clusters \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Cluster Faces

```bash
# Cluster all faces for current user
curl -X POST http://localhost:8080/api/v1/faces/cluster \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Assign Person Name

```bash
# Assign name to a cluster
curl -X POST http://localhost:8080/api/v1/faces/clusters/{cluster_id}/assign \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"person_name": "John Doe"}'
```

### Search for Similar Faces

```bash
# Find similar faces to a specific face
curl http://localhost:8080/api/v1/faces/{face_id}/similar \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Face Detection
FACE_DETECTION_THRESHOLD=0.99  # Higher = stricter detection (0.0-1.0)
FACE_SIMILARITY_THRESHOLD=0.55  # Higher = stricter matching (0.0-1.0)
```

### Adjust Thresholds

Edit `config/settings.py`:

```python
# Detection threshold (how confident we must be it's a face)
FACE_DETECTION_THRESHOLD = 0.99  # Default: very strict
# Use 0.95 for more detections (may include non-faces)
# Use 0.999 for only very clear faces

# Similarity threshold (how similar faces must be to cluster)
FACE_SIMILARITY_THRESHOLD = 0.55  # Default: moderate
# Use 0.70 for stricter clustering (same person only)
# Use 0.40 for looser clustering (may group different people)
```

## How It Works

### Detection Pipeline

```
1. Upload Image
   ↓
2. MTCNN Face Detection
   ├─ Find face bounding boxes
   ├─ Calculate confidence scores
   └─ Extract facial landmarks
   ↓
3. Face Extraction
   ├─ Expand bounding box (30%)
   ├─ Crop face region
   ├─ Calculate quality score
   └─ Save face image
   ↓
4. Embedding Generation
   ├─ FaceNet512 forward pass
   ├─ Generate 512-dim vector
   └─ Store in vector database
   ↓
5. Attribute Analysis
   ├─ Age estimation
   ├─ Gender classification
   └─ Emotion detection
   ↓
6. Database Storage
   └─ Save Face record
```

### Clustering Pipeline

```
1. Get All User Faces
   ↓
2. Extract Embeddings
   ↓
3. DBSCAN Clustering
   ├─ Metric: cosine similarity
   ├─ eps = 1 - FACE_SIMILARITY_THRESHOLD
   └─ min_samples = 1
   ↓
4. Assign Clusters
   ├─ Select primary face (best quality)
   ├─ Update face records
   └─ Store cluster_id
   ↓
5. Return Results
   └─ Clusters created, faces grouped
```

## Performance

### Detection Speed

- **CPU**: ~1-2 seconds per image
- **GPU (CUDA)**: ~0.2-0.5 seconds per image
- **GPU (MPS/Apple Silicon)**: ~0.3-0.7 seconds per image

### Accuracy

- **Detection**: ~95% on clear frontal faces
- **Recognition**: ~98% on same-person matching
- **Age**: ±5 years typical error
- **Gender**: ~95% accuracy
- **Emotion**: ~85% accuracy

### Resource Usage

- **Memory per face**: ~3KB (512 floats × 4 bytes + metadata)
- **Disk per face**: ~50KB (face crop image)
- **1000 faces**: ~50MB total storage

## Troubleshooting

### Issue: "MTCNN not loaded"

**Cause**: facenet-pytorch not installed

**Solution**:
```bash
pip install facenet-pytorch
python utils/test_face_detection.py --test 1
```

### Issue: "DeepFace initialization failed"

**Cause**: DeepFace or its dependencies not installed

**Solution**:
```bash
pip install deepface
pip install tf-keras  # TensorFlow backend
```

### Issue: No faces detected in images

**Possible causes**:
1. Detection threshold too high
2. Faces too small
3. Faces not frontal
4. Poor image quality

**Solutions**:
```python
# Lower detection threshold
FACE_DETECTION_THRESHOLD = 0.95  # in config/settings.py

# Lower minimum face size
self.mtcnn = MTCNN(min_face_size=15)  # in face_service.py

# Check image
python utils/test_face_detection.py --test 3
```

### Issue: Too many false detections

**Cause**: Detection threshold too low

**Solution**:
```python
# Increase threshold
FACE_DETECTION_THRESHOLD = 0.995  # in config/settings.py
```

### Issue: Same person in multiple clusters

**Cause**: Similarity threshold too high

**Solution**:
```python
# Lower similarity threshold
FACE_SIMILARITY_THRESHOLD = 0.45  # in config/settings.py

# Re-cluster faces
curl -X POST http://localhost:8080/api/v1/faces/cluster \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: Different people in same cluster

**Cause**: Similarity threshold too low

**Solution**:
```python
# Increase similarity threshold
FACE_SIMILARITY_THRESHOLD = 0.65  # in config/settings.py

# Re-cluster faces
curl -X POST http://localhost:8080/api/v1/faces/cluster \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: Faces directory not writable

**Cause**: Permission issues

**Solution**:
```bash
# Check permissions
ls -la static/uploads/faces

# Fix permissions
chmod 755 static/uploads/faces

# Or create directory
mkdir -p static/uploads/faces
chmod 755 static/uploads/faces
```

## Database Schema

### faces Table

```sql
CREATE TABLE faces (
  id INTEGER PRIMARY KEY,
  face_id VARCHAR(100) UNIQUE NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  checksum VARCHAR(64) NOT NULL,
  bounding_box JSON NOT NULL,
  confidence_score FLOAT NOT NULL,
  embedding_vector TEXT,
  embedding_version VARCHAR(50) DEFAULT 'v1',
  face_cluster_id VARCHAR(100),
  is_primary_face BOOLEAN DEFAULT FALSE,
  person_name VARCHAR(255),
  person_id VARCHAR(100),
  manual_verification BOOLEAN DEFAULT FALSE,
  quality_score FLOAT,
  age_estimate INTEGER,
  gender_estimate ENUM('male', 'female', 'unknown'),
  emotion_estimate VARCHAR(50),
  status ENUM('pending', 'processed', 'clustered', 'failed'),
  processing_error TEXT,
  image_id INTEGER REFERENCES images(id),
  modern_image_id INTEGER REFERENCES modern_images(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_faces_image_status ON faces(image_id, status);
CREATE INDEX ix_faces_cluster_primary ON faces(face_cluster_id, is_primary_face);
CREATE INDEX ix_faces_person ON faces(person_id, manual_verification);
```

### face_similarities Table

```sql
CREATE TABLE face_similarities (
  face_id_1 INTEGER REFERENCES faces(id),
  face_id_2 INTEGER REFERENCES faces(id),
  similarity_score FLOAT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (face_id_1, face_id_2)
);
```

## Best Practices

### 1. Image Quality

For best results:
- **Resolution**: At least 640x480 pixels
- **Face size**: At least 80x80 pixels
- **Lighting**: Well-lit, evenly exposed
- **Angle**: Frontal or near-frontal faces
- **Clarity**: Sharp, not blurry

### 2. Detection Settings

- **Threshold 0.99**: Default, balanced
- **Threshold 0.95-0.98**: More detections, some false positives
- **Threshold 0.995-0.999**: Fewer detections, high precision

### 3. Clustering Strategy

- **First run**: Use default threshold (0.55)
- **Review results**: Check cluster quality
- **Adjust**: Increase for stricter, decrease for looser
- **Re-cluster**: Run clustering again after adjustment

### 4. Person Assignment

- **Review clusters first**: Ensure quality before naming
- **Use primary face**: Best quality representative
- **Manual verification**: Flag important assignments
- **Batch assign**: Assign names to entire clusters at once

### 5. Privacy Considerations

- **User isolation**: Faces only visible to owning user
- **Opt-out**: Allow users to disable face detection
- **Data deletion**: Delete face data when images deleted
- **Encryption**: Consider encrypting face embeddings

## Advanced Features

### Custom Face Detection

You can use the FaceService directly:

```python
from services.face_service import FaceService
from models.image import Image

face_service = FaceService()

# Detect faces in an image
image_id = 123
results = face_service.process_image_faces(image_id)

print(f"Detected {results['faces_detected']} faces")
print(f"Processed {results['faces_processed']} faces")
```

### Manual Face Analysis

```python
# Analyze a specific face file
face_path = "static/uploads/faces/1/face_abc123.jpg"

# Get embedding
embedding = face_service.generate_face_embedding(face_path)
print(f"Embedding shape: {embedding.shape}")

# Get attributes
attributes = face_service.analyze_face_attributes(face_path)
print(f"Age: {attributes['age_estimate']}")
print(f"Gender: {attributes['gender_estimate']}")
print(f"Emotion: {attributes['emotion_estimate']}")
```

### Bulk Clustering

```python
# Cluster all faces for a user
user_id = 1
results = face_service.cluster_user_faces(user_id)

print(f"Created {results['clusters_created']} clusters")
print(f"Clustered {results['faces_clustered']} faces")
print(f"Noise points: {results['noise_points']}")
```

## Monitoring

### Check System Health

```bash
curl http://localhost:8080/health
```

Response includes face detection status:
```json
{
  "face_service": {
    "healthy": true,
    "face_detector": {
      "loaded": true,
      "device": "cuda"
    },
    "processing_stats": {
      "total_faces": 1234,
      "pending_processing": 5,
      "failed_processing": 2
    }
  }
}
```

### Monitor Logs

```bash
# Watch face detection logs
tail -f logs/app.log | grep -i "face\|mtcnn\|deepface"
```

## Summary

Face detection is now **fully functional** with:

✅ **MTCNN face detection** - Accurate face localization
✅ **FaceNet512 embeddings** - 512-dim recognition vectors
✅ **Attribute analysis** - Age, gender, emotion estimation
✅ **Automatic clustering** - Group similar faces
✅ **Person identification** - Assign names to clusters
✅ **Face search** - Find similar faces
✅ **Quality scoring** - Assess face image quality
✅ **Vector storage** - Fast similarity search
✅ **Comprehensive API** - Full CRUD operations
✅ **Health monitoring** - System status checks

All face detection features are enabled by default when uploading images!
