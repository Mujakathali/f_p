#!/usr/bin/env python3
"""
CLIP Image Processing Module for MemoryGraph AI
Handles image encoding, captioning, and semantic search using CLIP
"""
import torch
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import numpy as np
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
import shutil
from datetime import datetime
import uuid

class CLIPImageProcessor:
    def __init__(self):
        self.clip_model = None
        self.clip_processor = None
        self.blip_model = None
        self.blip_processor = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_loaded = False
        
        # Image storage directory
        self.image_storage_dir = "./stored_images"
        os.makedirs(self.image_storage_dir, exist_ok=True)

    async def load_models(self):
        """Load CLIP and BLIP models"""
        try:
            print("🔄 Loading CLIP model for image processing...")
            
            # Get Hugging Face token
            hf_token = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HUGGINGFACE_TOKEN')
            
            # Load CLIP model
            loop = asyncio.get_event_loop()
            
            try:
                # Load CLIP ViT-B/32
                self.clip_model = await loop.run_in_executor(
                    self.executor,
                    lambda: CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_auth_token=hf_token)
                )
                self.clip_processor = await loop.run_in_executor(
                    self.executor,
                    lambda: CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_auth_token=hf_token)
                )
                print("✅ CLIP model loaded successfully")
                
                # Load BLIP for image captioning
                self.blip_model = await loop.run_in_executor(
                    self.executor,
                    lambda: BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", use_auth_token=hf_token)
                )
                self.blip_processor = await loop.run_in_executor(
                    self.executor,
                    lambda: BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_auth_token=hf_token)
                )
                print("✅ BLIP captioning model loaded successfully")
                
            except Exception as e:
                print(f"⚠️ Failed to load advanced models: {e}")
                # Fallback to basic CLIP only
                self.clip_model = await loop.run_in_executor(
                    self.executor,
                    lambda: CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                )
                self.clip_processor = await loop.run_in_executor(
                    self.executor,
                    lambda: CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                )
                print("✅ Basic CLIP model loaded as fallback")
            
            self.is_loaded = True
            print("✅ Image processing models initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to load image processing models: {e}")
            raise

    async def store_image_locally(self, temp_image_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Store image locally and return storage info"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(temp_image_path)[1].lower()
            
            stored_filename = f"img_{timestamp}_{unique_id}{file_extension}"
            stored_path = os.path.join(self.image_storage_dir, stored_filename)
            
            # Copy image to storage directory
            shutil.copy2(temp_image_path, stored_path)
            
            # Get image metadata
            image = Image.open(stored_path)
            width, height = image.size
            file_size = os.path.getsize(stored_path)
            
            storage_info = {
                "stored_path": stored_path,
                "filename": stored_filename,
                "width": width,
                "height": height,
                "file_size": file_size,
                "format": image.format,
                "mode": image.mode,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"💾 Image stored locally: {stored_filename} ({width}x{height})")
            return storage_info
            
        except Exception as e:
            print(f"❌ Failed to store image locally: {e}")
            return {"error": str(e)}

    async def generate_caption(self, image_path: str) -> Dict[str, Any]:
        """Generate caption for image using BLIP"""
        if not self.is_loaded:
            await self.load_models()
        
        try:
            loop = asyncio.get_event_loop()
            
            if self.blip_model and self.blip_processor:
                # Use BLIP for detailed captioning
                result = await loop.run_in_executor(
                    self.executor,
                    self._generate_blip_caption,
                    image_path
                )
            else:
                # Fallback to basic description
                result = {
                    "caption": "Image uploaded successfully",
                    "confidence": 0.5,
                    "source": "fallback"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Caption generation failed: {e}")
            return {
                "caption": "Image uploaded (caption generation failed)",
                "confidence": 0.0,
                "source": "error",
                "error": str(e)
            }

    def _generate_blip_caption(self, image_path: str) -> Dict[str, Any]:
        """Generate caption using BLIP model (sync)"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Generate caption
            inputs = self.blip_processor(image, return_tensors="pt")
            
            with torch.no_grad():
                out = self.blip_model.generate(**inputs, max_length=50, num_beams=5)
            
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            return {
                "caption": caption,
                "confidence": 0.85,
                "source": "blip"
            }
            
        except Exception as e:
            raise Exception(f"BLIP caption generation failed: {e}")

    async def encode_image(self, image_path: str) -> List[float]:
        """Encode image using CLIP to get embedding vector"""
        if not self.is_loaded:
            await self.load_models()
        
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._encode_image_sync,
                image_path
            )
            return embedding.tolist()
            
        except Exception as e:
            print(f"❌ Image encoding failed: {e}")
            return []

    def _encode_image_sync(self, image_path: str) -> np.ndarray:
        """Encode image using CLIP (sync)"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Process image
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            # Get image features
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.squeeze().numpy()
            
        except Exception as e:
            raise Exception(f"CLIP encoding failed: {e}")

    async def search_similar_images(self, query_text: str, stored_embeddings: List[Dict]) -> List[Dict]:
        """Search for images similar to text query using CLIP"""
        if not self.is_loaded:
            await self.load_models()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Encode text query
            text_embedding = await loop.run_in_executor(
                self.executor,
                self._encode_text_sync,
                query_text
            )
            
            # Calculate similarities
            similarities = []
            for item in stored_embeddings:
                if 'embedding' in item:
                    image_embedding = np.array(item['embedding'])
                    similarity = np.dot(text_embedding, image_embedding)
                    similarities.append({
                        **item,
                        'similarity': float(similarity)
                    })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities
            
        except Exception as e:
            print(f"❌ Image search failed: {e}")
            return []

    def _encode_text_sync(self, text: str) -> np.ndarray:
        """Encode text using CLIP (sync)"""
        try:
            # Process text
            inputs = self.clip_processor(text=[text], return_tensors="pt", padding=True)
            
            # Get text features
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
                # Normalize features
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.squeeze().numpy()
            
        except Exception as e:
            raise Exception(f"Text encoding failed: {e}")

    async def validate_image_file(self, image_path: str) -> Dict[str, Any]:
        """Validate image file"""
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"valid": False, "error": "File does not exist"}
            
            # Check file size (max 10MB)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                return {"valid": False, "error": "File too large (max 10MB)"}
            
            # Try to open with PIL
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_name = img.format
                    
                    # Check dimensions
                    if width > 4096 or height > 4096:
                        return {"valid": False, "error": "Image dimensions too large (max 4096x4096)"}
                    
                    # Check format
                    allowed_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']
                    if format_name not in allowed_formats:
                        return {"valid": False, "error": f"Unsupported format: {format_name}"}
                    
                    return {
                        "valid": True,
                        "width": width,
                        "height": height,
                        "format": format_name,
                        "file_size": file_size
                    }
            
            except Exception as img_error:
                return {"valid": False, "error": f"Invalid image file: {img_error}"}
                
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {e}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "clip_loaded": self.clip_model is not None,
            "blip_loaded": self.blip_model is not None,
            "is_loaded": self.is_loaded,
            "storage_dir": self.image_storage_dir
        }
