#!/usr/bin/env python3
"""
Minimal server for testing image upload without heavy model loading
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil
from datetime import datetime
import uuid

app = FastAPI(title="Minimal MemoryGraph Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple image storage
IMAGE_STORAGE_DIR = "./test_images"
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Minimal MemoryGraph Server", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/api/v1/add_memory")
async def add_text_memory(request: dict):
    """Simple text memory endpoint"""
    print(f"📝 Received text memory: {request.get('text', '')}")
    return {
        "status": "success",
        "message": "Text memory processed",
        "id": 1,
        "processed_text": request.get('text', ''),
        "sentiment": {"label": "positive", "score": 0.8},
        "entities": [],
        "keywords": []
    }

@app.post("/api/v1/add_image_memory")
async def add_image_memory(
    image_file: UploadFile = File(...),
    caption: str = Form(""),
    metadata: str = Form("{}")
):
    """Simple image memory endpoint"""
    try:
        print(f"🖼️ Received image: {image_file.filename}")
        print(f"📝 Caption: {caption}")
        
        # Save image locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = os.path.splitext(image_file.filename)[1].lower()
        stored_filename = f"img_{timestamp}_{unique_id}{file_extension}"
        stored_path = os.path.join(IMAGE_STORAGE_DIR, stored_filename)
        
        # Save file
        with open(stored_path, "wb") as buffer:
            content = await image_file.read()
            buffer.write(content)
        
        print(f"💾 Image saved: {stored_path}")
        
        return {
            "status": "success",
            "message": "Image memory processed",
            "id": 2,
            "filename": stored_filename,
            "stored_path": stored_path,
            "caption": caption or "Image uploaded successfully",
            "sentiment": {"label": "positive", "score": 0.8},
            "entities": [],
            "keywords": []
        }
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal server...")
    print("📊 Features:")
    print("   • Image upload with preview")
    print("   • Caption support")
    print("   • Local image storage")
    print("   • No heavy model loading")
    uvicorn.run("minimal_server:app", host="127.0.0.1", port=8000, reload=True)
