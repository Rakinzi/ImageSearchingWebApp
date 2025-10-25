# Quick Reference Card

## 🚀 Instant Setup (5 Minutes)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install easyocr  # For OCR
flask db upgrade
python main.py &
celery -A main.celery worker --pool=solo &

# Frontend
cd frontend
npm install && npm run dev

# Open http://localhost:3000
```

## 🧪 Quick Tests

```bash
# Test everything
python utils/test_embeddings.py      # Embeddings ✅
python utils/test_face_detection.py  # Faces ✅
python utils/test_ocr.py             # OCR ✅

# Health check
curl http://localhost:8080/health
```

## 🎛️ Feature Toggles

**Frontend** (`UploadComponent.vue`):
```javascript
options.extractText        // OCR
options.detectFaces        // Face detection
options.generateEmbeddings // Embeddings
```

**Backend** (auto-processes based on toggles):
- `extract_text=true` → OCR runs
- `detect_faces=true` → Face detection runs
- `generate_embeddings=true` → CLIP embeddings generated

## 📊 System Status

| Feature | Status | Test Command |
|---------|--------|--------------|
| Embeddings | ✅ Fixed | `python utils/test_embeddings.py` |
| Face Detection | ✅ Working | `python utils/test_face_detection.py` |
| OCR | ✅ Working | `python utils/test_ocr.py` |
| Frontend Toggles | ✅ Added | Check upload page |

## 📝 Key Files Modified

**Backend**:
- `services/vector_service.py` - Fixed similarity calculation
- `services/image_service.py` - Enabled face detection & OCR
- `services/modern_image_service.py` - Enabled all features
- `utils/ocr.py` - NEW: OCR module
- `requirements.txt` - Added EasyOCR

**Frontend**:
- `components/UploadComponent.vue` - Added feature toggles
- `stores/imagesStore.js` - Passes toggles to API

## 🔧 Configuration

**Essential `.env` settings**:
```bash
# Database
DATABASE_URL=sqlite:///app.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Thresholds
FACE_DETECTION_THRESHOLD=0.99
FACE_SIMILARITY_THRESHOLD=0.55
IMAGE_SIMILARITY_THRESHOLD=0.85

# Vector DB
CHROMADB_PATH=./chroma_db
```

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| `COMPLETE_SUMMARY.md` | Full overview |
| `EMBEDDINGS_FIX.md` | Embeddings fixes |
| `FACE_DETECTION.md` | Face system |
| `OCR.md` | Text extraction |
| `CONFIGURATION.md` | All settings |
| `FEATURE_TOGGLES.md` | Frontend toggles |

## 🐛 Quick Troubleshooting

**No OCR backend?**
```bash
pip install easyocr
python utils/test_ocr.py --test 1
```

**Embeddings not working?**
```bash
python utils/test_embeddings.py
python utils/migrate_embeddings.py --action migrate --live
```

**Face detection failing?**
```bash
pip install facenet-pytorch deepface
python utils/test_face_detection.py --test 1
```

**Frontend toggles not working?**
- Check browser console for errors
- Verify API URL in frontend `.env`
- Check backend logs for received params

## 💡 Common Tasks

**Upload with specific features**:
```bash
curl -X POST http://localhost:8080/api/v2/images/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@image.jpg" \
  -F "extract_text=true" \
  -F "detect_faces=false" \
  -F "generate_embeddings=true"
```

**Search semantically**:
```bash
curl -X POST http://localhost:8080/api/v2/images/search \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "sunset", "search_type": "semantic"}'
```

**Get statistics**:
```bash
curl http://localhost:8080/api/v1/images/stats \
  -H "Authorization: Bearer TOKEN"
```

## ⚡ Performance Tips

**GPU Acceleration**:
```bash
# Check CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Runs automatically if GPU available
```

**Batch Processing**:
```python
# Upload multiple images at once
# Frontend handles this automatically
```

**Optimize Settings**:
```bash
# Faster processing, lower accuracy
FACE_DETECTION_THRESHOLD=0.95

# Slower processing, higher accuracy
FACE_DETECTION_THRESHOLD=0.999
```

## 🎯 Default Behaviors

All features **enabled by default**:
- ✅ Text extraction (OCR)
- ✅ Face detection
- ✅ Embedding generation

Users can toggle off unwanted features.

## 📞 Need Help?

1. Check `/health` endpoint
2. Review `logs/app.log`
3. Run test utilities
4. Consult documentation
5. Check `SYSTEM_STATUS.md`

---

**Status**: ✅ All systems operational
**Version**: 2.0.0
**Updated**: 2025-10-23
