# 🖼️ Image Embedding Storage & Search Guide

## ✅ **Issues Fixed**

### 1. **Neo4j Error Fixed** ✅
- **Problem**: `'Neo4jConnector' object has no attribute 'create_organization_node'`
- **Solution**: Added missing `create_organization_node` method to Neo4j connector

### 2. **Pydantic Serialization Error Fixed** ✅
- **Problem**: `Unable to serialize unknown type: <class 'numpy.float32'>`
- **Solution**: Added `convert_numpy_types()` function to convert numpy types to Python native types

### 3. **Image Search Integration** ✅
- **Problem**: Images not appearing in search results
- **Solution**: Enhanced search endpoint to include CLIP-based image search

## 📊 **Image Embedding Storage Locations**

### **1. ChromaDB - Image Embeddings Collection**
```python
# Location: ./chroma_db/image_embeddings/
# Dimensions: 512 (CLIP ViT-B/32)
# Collection Name: "image_embeddings"

{
    "id": "image_49_img_20250917_081010_f28c322c.jpg",
    "embedding": [0.1, 0.2, 0.3, ...],  # 512-dimensional CLIP vector
    "document": "Image: Beautiful sunset over mountains",
    "metadata": {
        "memory_id": 49,
        "type": "image",
        "image_path": "./stored_images/img_20250917_081010_f28c322c.jpg",
        "filename": "img_20250917_081010_f28c322c.jpg",
        "caption": "Beautiful sunset over mountains",
        "image_width": 1920,
        "image_height": 1080,
        "file_size": 245760
    }
}
```

### **2. ChromaDB - Text Embeddings Collection**
```python
# Location: ./chroma_db/text_embeddings/
# Dimensions: 768 (BGE-base-en-v1.5)
# Collection Name: "text_embeddings"

{
    "id": "memory_49_uuid",
    "embedding": [0.4, 0.5, 0.6, ...],  # 768-dimensional BGE vector
    "document": "Beautiful sunset over mountains",  # Caption text
    "metadata": {
        "memory_id": 49,
        "type": "text",
        "source": "image_caption"
    }
}
```

### **3. Local File System**
```bash
# Location: ./stored_images/
# File: img_20250917_081010_f28c322c.jpg
# Purpose: Original image file for display
```

### **4. PostgreSQL Database**
```sql
-- Table: memories
{
    "id": 49,
    "raw_text": "Beautiful sunset over mountains",  -- Caption
    "processed_text": "beautiful sunset mountain",      -- Cleaned caption
    "memory_type": "image",
    "metadata": {
        "image_path": "./stored_images/img_20250917_081010_f28c322c.jpg",
        "filename": "img_20250917_081010_f28c322c.jpg",
        "image_width": 1920,
        "image_height": 1080,
        "image_format": "JPEG",
        "file_size": 245760,
        "caption_source": "user"
    }
}
```

### **5. Neo4j Graph Database**
```cypher
-- Memory Node
(m:Memory {
    id: 49,
    text: "Beautiful sunset over mountains",
    type: "image",
    timestamp: "2025-01-17T08:10:10",
    emotion: "joy"
})

-- Entity Relationships
(m)-[:LOCATED_AT]->(l:Location {name: "mountains"})
```

## 🔍 **Search Capabilities**

### **1. Text-to-Image Search**
```bash
# API Call
GET /api/v1/search_memories?query=sunset&search_type=image

# Process:
1. Encode "sunset" with CLIP text encoder → 512d vector
2. Search image_embeddings collection in ChromaDB
3. Find similar image embeddings (cosine similarity)
4. Return matching images with metadata

# Response includes:
{
    "memories": [
        {
            "id": 49,
            "type": "image",
            "raw_text": "Beautiful sunset over mountains",
            "similarity_score": 0.85,
            "search_type": "image",
            "image_path": "./stored_images/img_20250917_081010_f28c322c.jpg",
            "filename": "img_20250917_081010_f28c322c.jpg"
        }
    ]
}
```

### **2. Hybrid Search (Text + Images)**
```bash
# API Call
GET /api/v1/search_memories?query=mountain photos&search_type=hybrid

# Process:
1. Keyword search in PostgreSQL
2. Semantic search in text_embeddings (768d BGE)
3. Image search in image_embeddings (512d CLIP)
4. Hybrid ranking with weighted scores:
   - Keywords: 30%
   - Semantic: 40% 
   - Images: 30%

# Returns: Combined results from all search types
```

### **3. Image-Only Search**
```bash
# API Call
GET /api/v1/search_memories?query=nature&search_type=image

# Process:
1. Only searches image_embeddings collection
2. Uses CLIP text encoder for query
3. Returns only image memories
```

## 🛠️ **How to Verify Image Storage**

### **Check ChromaDB Collections**
```python
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")

# List collections
collections = client.list_collections()
print("Collections:", [c.name for c in collections])

# Check image embeddings
image_collection = client.get_collection("image_embeddings")
print(f"Image embeddings count: {image_collection.count()}")

# Check text embeddings  
text_collection = client.get_collection("text_embeddings")
print(f"Text embeddings count: {text_collection.count()}")
```

### **Check Local Images**
```bash
ls -la ./stored_images/
# Should show: img_YYYYMMDD_HHMMSS_uuid.jpg files
```

### **Check PostgreSQL**
```sql
SELECT id, memory_type, raw_text, metadata->>'image_path' as image_path 
FROM memories 
WHERE memory_type = 'image';
```

### **Test Search API**
```bash
# Test image search
curl "http://localhost:8000/api/v1/search_memories?query=sunset&search_type=image"

# Test hybrid search
curl "http://localhost:8000/api/v1/search_memories?query=mountain&search_type=hybrid"
```

## 📈 **Search Flow Diagram**

```
User Query: "sunset photos"
         ↓
    Search Endpoint
         ↓
┌─────────────────────────────────────┐
│  1. Keyword Search (PostgreSQL)     │
│  2. Semantic Search (BGE 768d)      │
│  3. Image Search (CLIP 512d)        │
└─────────────────────────────────────┘
         ↓
    Hybrid Ranking
    (30% + 40% + 30%)
         ↓
    Combined Results
    ┌─────────────────┐
    │ Text Memories   │
    │ Image Memories  │ ← Images included!
    │ Mixed Results   │
    └─────────────────┘
```

## 🎯 **Key Features Now Working**

1. ✅ **Images stored in 5 locations** (ChromaDB, PostgreSQL, Local files, Neo4j)
2. ✅ **CLIP embeddings** (512d) separate from text embeddings (768d)
3. ✅ **Text-to-image search** using CLIP text encoder
4. ✅ **Hybrid search** combining text and image results
5. ✅ **Image metadata** included in search results
6. ✅ **No more serialization errors** (numpy types converted)
7. ✅ **No more Neo4j errors** (missing methods added)

## 🚀 **Usage Examples**

### **Search for Images**
```javascript
// Frontend API call
const results = await ApiService.searchMemories("sunset", 10, "image");
// Returns: Only image memories with image_path and filename

const results = await ApiService.searchMemories("mountain", 10, "hybrid");  
// Returns: Text + Image memories ranked by relevance
```

### **Display Image Results**
```javascript
// In frontend, check if result has image
if (memory.type === 'image' && memory.image_path) {
    // Display image preview
    <img src={`/api/images/${memory.filename}`} alt={memory.raw_text} />
}
```

Your images are now fully integrated into the search system! 🎉
