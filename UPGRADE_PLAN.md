# Vector Search Upgrade Plan

## Overview
This document outlines the plan to upgrade the image search system from the basic OpenAI CLIP model with ChromaDB to a more efficient OpenCLIP model with PostgreSQL pgvector integration.

## Current System Issues

### 1. Model Performance
- **Current Model**: OpenAI CLIP ViT-B/32
- **Embedding Dimension**: 512
- **ImageNet Accuracy**: ~63%
- **Problem**: Low similarity scores (0.6) even for semantically relevant matches
- **Root Cause**: Smaller model with limited semantic understanding

### 2. Storage Architecture
- **Current**: ChromaDB as separate vector database
- **Problem**: Additional service to maintain, separate from main PostgreSQL database
- **Concern**: Increased complexity and potential sync issues

## Proposed Solutions

### 1. Model Upgrade: OpenCLIP ViT-L/14

**Selected Model**: `laion/CLIP-ViT-L-14-laion2B-s32B-b82K`

**Specifications**:
- Embedding Dimension: 768 (vs current 512)
- ImageNet Zero-shot Accuracy: 75.3% (vs current ~63%)
- Training Dataset: LAION-2B (2 billion image-text pairs)
- Performance Improvement: ~12% better accuracy

**Why ViT-L/14?**:
- Best balance between performance and resource usage
- 50% larger embeddings (768 vs 512) = better semantic representation
- Proven track record for image retrieval tasks
- Significantly better at understanding text-to-image relationships

**Alternative Options**:
- **ViT-H/14**: 1024-dim, 78.0% accuracy (requires more GPU/CPU resources)
- **ViT-g/14**: 1024-dim, 78.4% accuracy (highest accuracy, most resource-intensive)
- **ViT-bigG/14**: 1024-dim, 80.1% accuracy (best but very resource-heavy)

### 2. Storage Upgrade: pgvector

**What is pgvector?**:
- PostgreSQL extension for vector similarity search
- Native support for vector operations and indexing
- Cosine similarity distance metric (same as ChromaDB)

**Benefits**:
- ✅ **Unified Database**: Store vectors in existing PostgreSQL
- ✅ **Better Performance**: HNSW indexing for fast approximate nearest neighbor search
- ✅ **Simpler Architecture**: No separate ChromaDB service
- ✅ **SQL Integration**: Combine vector search with complex SQL queries
- ✅ **ACID Compliance**: Transactional guarantees for vector operations
- ✅ **Cosine Similarity**: Native support for `<=>` operator

**Indexing Options**:
- **IVFFlat**: Faster build time, good for smaller datasets
- **HNSW**: Better query performance, recommended for production

## Implementation Plan

### Phase 1: Preparation ✅

**Status**: Completed

- [x] Research best CLIP models for 2024-2025
- [x] Evaluate OpenCLIP variants (ViT-L/14, ViT-H/14, ViT-g/14)
- [x] Research pgvector capabilities and integration
- [x] Document upgrade plan

### Phase 2: Dependencies Update

**Tasks**:
1. Update `requirements.txt` to replace OpenAI CLIP with `open-clip-torch`
2. Add `pgvector` Python package
3. Update Docker Compose to install pgvector PostgreSQL extension

**Files to Modify**:
- `backend/requirements.txt`
- `backend/docker-compose.simple.yml`
- `backend/Dockerfile`

### Phase 3: Database Schema Changes

**Tasks**:
1. Create Flask-Migrate migration to add pgvector extension
2. Add `embedding` column (vector(768)) to `modern_images` table
3. Create HNSW index on embedding column for fast similarity search

**SQL Operations**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column
ALTER TABLE modern_images
ADD COLUMN embedding vector(768);

-- Create HNSW index for cosine similarity
CREATE INDEX modern_images_embedding_idx
ON modern_images
USING hnsw (embedding vector_cosine_ops);
```

**Files to Create**:
- Migration file via `flask db migrate -m "Add pgvector support"`

### Phase 4: VectorService Refactor

**Tasks**:
1. Update CLIP model initialization to use OpenCLIP ViT-L/14
2. Replace ChromaDB operations with pgvector queries
3. Update embedding dimension constant (512 → 768)
4. Implement cosine similarity search using SQLAlchemy + pgvector
5. Update all vector storage/retrieval methods

**Key Changes**:
```python
# Before (OpenAI CLIP)
import clip
model, preprocessor = clip.load('ViT-B/32', device=device)

# After (OpenCLIP)
import open_clip
model, _, preprocessor = open_clip.create_model_and_transforms(
    'ViT-L-14',
    pretrained='laion2b_s32b_b82k'
)
```

**Files to Modify**:
- `backend/services/vector_service.py`

### Phase 5: Model Schema Updates

**Tasks**:
1. Update `ModernImage` model to include embedding field
2. Add pgvector similarity search methods to model
3. Remove ChromaDB-specific fields (vector_id)

**Files to Modify**:
- `backend/models/modern_image.py`

### Phase 6: Data Migration

**Tasks**:
1. Create migration script to:
   - Load existing ChromaDB vectors
   - Re-generate embeddings using new ViT-L/14 model (recommended for best accuracy)
   - OR transfer existing vectors + re-pad to 768-dim (faster but less accurate)
   - Store in PostgreSQL pgvector
2. Verify all images have embeddings
3. Test similarity search with sample queries

**Files to Create**:
- `backend/utils/migrate_to_pgvector.py`

**Migration Options**:
- **Option A (Recommended)**: Regenerate all embeddings with new model
  - Pros: Best accuracy, clean start
  - Cons: Takes time for large datasets
- **Option B**: Pad existing 512-dim to 768-dim
  - Pros: Faster migration
  - Cons: Suboptimal embeddings, lower accuracy

### Phase 7: Testing & Validation

**Tasks**:
1. Test text-to-image search with new model
2. Verify similarity scores are improved (higher for relevant matches)
3. Test metadata + vector hybrid search
4. Performance benchmarks (query speed with HNSW index)
5. Verify public test endpoint works

**Test Cases**:
- Search "tea" → Should return tea images with high similarity (>0.7)
- Search "person in red shirt" → Semantic understanding test
- Date + semantic search combination
- Compare old vs new similarity scores

### Phase 8: Cleanup

**Tasks**:
1. Remove ChromaDB dependencies from requirements.txt
2. Remove ChromaDB data directory
3. Update documentation (CLAUDE.md)
4. Remove unused vector service methods

## Expected Results

### Performance Improvements
- **Similarity Scores**: More meaningful scores (0.7-0.9 for good matches vs current 0.5-0.6)
- **Search Accuracy**: 12-15% improvement in semantic understanding
- **Query Speed**: Faster with HNSW indexing (~10-50ms per query)

### Architecture Benefits
- **Simplified Stack**: One database instead of two (PostgreSQL vs PostgreSQL + ChromaDB)
- **Easier Maintenance**: Native SQL integration
- **Better Scalability**: PostgreSQL's proven scalability

### Resource Usage
- **Model Size**: ViT-L/14 is larger (~400MB vs ~150MB for ViT-B/32)
- **Embedding Storage**: 768-dim vs 512-dim (50% larger per image)
- **Memory**: Slightly higher during inference

## Rollback Plan

If issues arise during upgrade:

1. **Keep ChromaDB data** until migration is verified
2. **Backup PostgreSQL** before schema changes
3. **Version control** all code changes
4. **Test endpoint** allows testing new system without affecting auth'd users

## Timeline Estimate

- **Phase 1**: ✅ Completed
- **Phase 2**: 15 minutes (dependencies)
- **Phase 3**: 30 minutes (database schema)
- **Phase 4**: 1-2 hours (VectorService refactor)
- **Phase 5**: 30 minutes (model updates)
- **Phase 6**: Variable (depends on dataset size, 1-4 hours)
- **Phase 7**: 1 hour (testing)
- **Phase 8**: 30 minutes (cleanup)

**Total**: ~4-6 hours of development + migration time

## Technical References

### OpenCLIP Resources
- [LAION OpenCLIP Models](https://github.com/mlfoundations/open_clip)
- [ViT-L/14 Model Card](https://huggingface.co/laion/CLIP-ViT-L-14-laion2B-s32B-b82K)
- [OpenCLIP Performance Benchmarks](https://laion.ai/blog/large-openclip/)

### pgvector Resources
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector Python Documentation](https://github.com/pgvector/pgvector-python)
- [PostgreSQL Vector Operations](https://www.postgresql.org/docs/current/functions-vector.html)

## Notes

- **Cosine Similarity**: Both ChromaDB and pgvector use cosine similarity
- **Distance Metric**: pgvector `<=>` operator for cosine distance (0 = identical, 2 = opposite)
- **Normalization**: Embeddings should be L2-normalized before storage (already done in current code)
- **HNSW Parameters**: Default parameters work well, can tune `m` and `ef_construction` if needed

## Success Criteria

✅ All images have 768-dimensional embeddings in PostgreSQL
✅ Similarity scores >0.7 for semantically relevant matches
✅ Search queries complete in <100ms
✅ Test endpoint returns accurate results
✅ No ChromaDB dependency remaining
✅ All existing features work (upload, search, metadata filtering)

---

**Created**: 2025-01-27
**Status**: In Progress
**Priority**: High
**Impact**: Significant improvement to core search functionality
