# Frontend Feature Toggles

## Overview

The upload interface now includes **visual toggles** for all AI processing features, giving users full control over which features are applied to their images.

## Features Added

### ✅ Processing Options UI

**Location**: `src/components/UploadComponent.vue`

The upload component now displays three feature toggles:

1. **Extract Text (OCR)** - Optical character recognition
2. **Detect Faces** - Face detection and analysis
3. **Generate AI Embeddings** - Semantic search embeddings

### UI Components

**Toggle Cards with Icons**:
- Each option has a descriptive icon
- Clear labels and descriptions
- All enabled by default

**Visual Feedback**:
- Info alert when features are enabled
- Warning alert when all features are disabled
- Real-time status updates

### Default Settings

All features are **enabled by default**:
```javascript
const options = reactive({
  extractText: true,       // OCR enabled
  detectFaces: true,       // Face detection enabled
  generateEmbeddings: true // Embeddings enabled
})
```

## How It Works

### 1. User Interface

```
┌─────────────────────────────────────────┐
│  Processing Options                     │
│  Select which AI features to apply      │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ ☑ Extract Text (OCR)              │ │
│  │   Detect and extract text from    │ │
│  │   images using OCR                │ │
│  │                                   │ │
│  │ ☑ Detect Faces                    │ │
│  │   Identify and analyze faces with │ │
│  │   age, gender, emotion detection  │ │
│  │                                   │ │
│  │ ☑ Generate AI Embeddings          │ │
│  │   Create AI-powered embeddings    │ │
│  │   for semantic search             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ℹ Processing enabled                  │
│  Selected features will be applied     │
│  in the background                     │
└─────────────────────────────────────────┘
```

### 2. Data Flow

```
User toggles features
    ↓
Options stored in component state
    ↓
Passed to imagesStore.uploadImages()
    ↓
Sent as FormData to API
    ↓
Backend processes based on flags
```

### 3. API Integration

**Store Implementation** (`src/stores/imagesStore.js` line 170-173):

```javascript
// V2 endpoint - add boolean options explicitly
formData.append('extract_text', options.extractText !== false ? 'true' : 'false')
formData.append('detect_faces', options.detectFaces !== false ? 'true' : 'false')
formData.append('generate_embeddings', options.generateEmbeddings !== false ? 'true' : 'false')
```

**API Payload Example**:
```
POST /api/v2/images/upload
Content-Type: multipart/form-data

files: [File, File, ...]
extract_text: true
detect_faces: true
generate_embeddings: true
metadata: {"tags": ["vacation"], "description": "Summer photos"}
```

## User Experience

### Visual States

**All Features Enabled (Default)**:
```
ℹ️ Processing enabled
Selected features will be applied in the background.
You can view results once processing completes.
```

**All Features Disabled**:
```
⚠️ All processing disabled
Images will be uploaded but no AI processing will occur.
You can reprocess images later.
```

### Upload Flow

1. **Select Images**: Drag & drop or click to select
2. **Configure Features**: Toggle desired processing options
3. **Add Metadata** (optional): Tags, description, location
4. **Upload**: Click upload button
5. **Background Processing**: Features process asynchronously
6. **View Results**: Check images once processing completes

## Feature Descriptions

### 📝 Extract Text (OCR)

**What it does**:
- Detects text in images using optical character recognition
- Supports multiple OCR backends (EasyOCR, PaddleOCR, Tesseract)
- Extracts text from documents, screenshots, signs, etc.

**Use cases**:
- Digitize documents
- Extract text from receipts/invoices
- Search images by text content
- Archive scanned documents

**Performance**:
- ~1-3 seconds per image (depending on backend)
- GPU acceleration supported
- Text becomes searchable immediately

### 👤 Detect Faces

**What it does**:
- Identifies faces using MTCNN detector
- Generates 512-dim FaceNet embeddings
- Analyzes age, gender, and emotion
- Automatically clusters similar faces

**Use cases**:
- Organize photos by person
- Find all images of a specific person
- Analyze photo collections
- Create face-based albums

**Performance**:
- ~1-2 seconds per image
- GPU acceleration supported
- Clustering available after detection

### 🔍 Generate AI Embeddings

**What it does**:
- Creates 512-dim CLIP embeddings
- Enables semantic image search
- Powers similarity matching
- Text-to-image search capability

**Use cases**:
- "Find images of sunset"
- "Show me photos with mountains"
- Find visually similar images
- Content-based image retrieval

**Performance**:
- ~0.3-2 seconds per image
- GPU significantly faster
- Instant search once generated

## Benefits of Toggles

### For Users

✅ **Control**: Choose which features matter for each upload
✅ **Speed**: Disable unneeded features for faster uploads
✅ **Privacy**: Opt out of face detection if desired
✅ **Flexibility**: Different settings for different image types

### For System

✅ **Efficiency**: Skip unnecessary processing
✅ **Resources**: Save compute on disabled features
✅ **Scalability**: Better resource allocation
✅ **Cost**: Reduce GPU/CPU usage

## Use Cases

### Scenario 1: Document Upload

**Settings**:
- ✅ Extract Text (OCR)
- ❌ Detect Faces
- ✅ Generate AI Embeddings

**Why**: Documents rarely have faces but need text extraction

### Scenario 2: Portrait Photos

**Settings**:
- ❌ Extract Text (OCR)
- ✅ Detect Faces
- ✅ Generate AI Embeddings

**Why**: Focus on face detection, text unlikely

### Scenario 3: Quick Backup

**Settings**:
- ❌ Extract Text (OCR)
- ❌ Detect Faces
- ❌ Generate AI Embeddings

**Why**: Just store images, process later

### Scenario 4: Full Processing (Default)

**Settings**:
- ✅ Extract Text (OCR)
- ✅ Detect Faces
- ✅ Generate AI Embeddings

**Why**: Maximum features, best search capabilities

## Technical Details

### Component Structure

```vue
<template>
  <n-upload ...>...</n-upload>

  <n-space vertical>
    <!-- Processing Options -->
    <n-card>
      <n-checkbox v-model:checked="options.extractText">
        Extract Text (OCR)
      </n-checkbox>
      <n-checkbox v-model:checked="options.detectFaces">
        Detect Faces
      </n-checkbox>
      <n-checkbox v-model:checked="options.generateEmbeddings">
        Generate AI Embeddings
      </n-checkbox>
    </n-card>

    <!-- Status Alert -->
    <n-alert v-if="featuresEnabled" type="info">
      Processing enabled
    </n-alert>
  </n-space>

  <!-- Metadata & Upload Button -->
</template>

<script setup>
const options = reactive({
  extractText: true,
  detectFaces: true,
  generateEmbeddings: true
})

const startUpload = async () => {
  await imagesStore.uploadImages(files, options)
}
</script>
```

### State Management

**Component State** → **Store State** → **API Request**

```javascript
// Component (UploadComponent.vue)
const options = reactive({
  extractText: true,
  detectFaces: true,
  generateEmbeddings: true
})

// Store (imagesStore.js)
async uploadImages(files, options) {
  formData.append('extract_text', options.extractText ? 'true' : 'false')
  // ... send to API
}

// API (backend)
@bp.route('/upload', methods=['POST'])
def upload():
    extract_text = request.form.get('extract_text', 'true') == 'true'
    detect_faces = request.form.get('detect_faces', 'true') == 'true'
    generate_embeddings = request.form.get('generate_embeddings', 'true') == 'true'
    # ... process with flags
```

## Future Enhancements

Possible future additions:

1. **Processing Profiles**
   - Save favorite combinations
   - Quick-select presets
   - User-defined templates

2. **Batch Settings**
   - Different settings per folder
   - Conditional processing rules
   - Auto-detect image type

3. **Advanced Options**
   - Confidence thresholds
   - OCR language selection
   - Custom processing parameters

4. **Cost Estimation**
   - Show estimated processing time
   - Resource usage preview
   - Credit/quota display

5. **Processing Queue**
   - View pending processes
   - Cancel in-progress tasks
   - Retry failed processes

## Accessibility

The toggles are fully accessible:

✅ Keyboard navigation
✅ Screen reader support
✅ Clear visual states
✅ Descriptive labels
✅ Hover tooltips (via Naive UI)

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Testing

To test the toggles:

1. Navigate to upload page
2. Select images
3. Toggle features on/off
4. Upload and verify in backend logs
5. Check processed results

**Expected Log Output**:
```
INFO: Text extraction: True
INFO: Face detection: False
INFO: Embeddings generation: True
```

## Summary

✅ **User-friendly toggles** for all AI features
✅ **Visual feedback** with icons and descriptions
✅ **Proper defaults** (all enabled)
✅ **Flexible control** per upload
✅ **Seamless integration** with backend
✅ **Clear communication** of what each feature does

Users now have full control over which AI features are applied to their images!
