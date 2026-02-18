#!/usr/bin/env python3
"""
Image serving routes for MemoryGraph AI
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

image_router = APIRouter()

# Image storage directory
IMAGE_STORAGE_DIR = "./stored_images"

@image_router.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve stored images"""
    try:
        # Validate filename (security check)
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check if file exists
        file_path = os.path.join(IMAGE_STORAGE_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Validate it's actually in our storage directory (security)
        real_path = os.path.realpath(file_path)
        storage_path = os.path.realpath(IMAGE_STORAGE_DIR)
        if not real_path.startswith(storage_path):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return the image file
        return FileResponse(
            file_path,
            media_type="image/jpeg",  # Default to JPEG, could be enhanced to detect type
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")

@image_router.get("/images/{filename}/info")
async def get_image_info(filename: str):
    """Get image metadata"""
    try:
        # Validate filename
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = os.path.join(IMAGE_STORAGE_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get file stats
        stat = os.stat(file_path)
        
        # Try to get image dimensions
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
        except:
            width, height, format_name = None, None, None
        
        return {
            "filename": filename,
            "file_size": stat.st_size,
            "width": width,
            "height": height,
            "format": format_name,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image info: {str(e)}")

@image_router.get("/images")
async def list_images(limit: int = 50, offset: int = 0):
    """List all stored images"""
    try:
        if not os.path.exists(IMAGE_STORAGE_DIR):
            return {"images": [], "total": 0}
        
        # Get all image files
        image_files = []
        for filename in os.listdir(IMAGE_STORAGE_DIR):
            file_path = os.path.join(IMAGE_STORAGE_DIR, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                stat = os.stat(file_path)
                image_files.append({
                    "filename": filename,
                    "file_size": stat.st_size,
                    "created": stat.st_ctime,
                    "url": f"/api/v1/images/{filename}"
                })
        
        # Sort by creation time (newest first)
        image_files.sort(key=lambda x: x["created"], reverse=True)
        
        # Apply pagination
        total = len(image_files)
        paginated = image_files[offset:offset + limit]
        
        return {
            "images": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")
