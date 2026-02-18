"""
Image processing module using Tesseract OCR for text extraction
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import tempfile
import os
from typing import Dict, Any, Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64
import io

class ImageProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        # Set Tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    async def extract_text_from_image(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        """Extract text from image using Tesseract OCR"""
        try:
            # Run OCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._extract_text_sync,
                image_path,
                language
            )
            
            return result
            
        except Exception as e:
            print(f"❌ OCR extraction failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "language": language,
                "error": str(e)
            }

    def _extract_text_sync(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        """Synchronous OCR extraction"""
        # Load and preprocess image
        processed_image = self._preprocess_image(image_path)
        
        # Extract text with detailed data
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?;:-'
        
        # Get text
        text = pytesseract.image_to_string(processed_image, lang=language, config=custom_config)
        
        # Get detailed data for confidence calculation
        data = pytesseract.image_to_data(processed_image, lang=language, output_type=pytesseract.Output.DICT)
        
        # Calculate confidence
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Get word count
        words = [word for word in data['text'] if word.strip()]
        
        return {
            "text": text.strip(),
            "confidence": avg_confidence / 100.0,  # Convert to 0-1 scale
            "word_count": len(words),
            "language": language,
            "bounding_boxes": self._extract_bounding_boxes(data)
        }

    def _preprocess_image(self, image_path: str) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Load image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance image for better OCR
        image = self._enhance_image(image)
        
        return image

    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for OCR"""
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to PIL Image
        enhanced_image = Image.fromarray(cleaned)
        
        # Additional PIL enhancements
        enhanced_image = enhanced_image.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(enhanced_image)
        enhanced_image = enhancer.enhance(1.5)
        
        return enhanced_image

    def _extract_bounding_boxes(self, ocr_data: Dict) -> List[Dict]:
        """Extract bounding box information for detected text"""
        boxes = []
        n_boxes = len(ocr_data['level'])
        
        for i in range(n_boxes):
            if int(ocr_data['conf'][i]) > 30:  # Only include confident detections
                box = {
                    "text": ocr_data['text'][i],
                    "confidence": int(ocr_data['conf'][i]) / 100.0,
                    "left": int(ocr_data['left'][i]),
                    "top": int(ocr_data['top'][i]),
                    "width": int(ocr_data['width'][i]),
                    "height": int(ocr_data['height'][i])
                }
                boxes.append(box)
        
        return boxes

    async def process_image_bytes(self, image_bytes: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
        """Process image from bytes"""
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Extract text from temporary file
            result = await self.extract_text_from_image(temp_file_path)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def process_base64_image(self, base64_string: str) -> Dict[str, Any]:
        """Process image from base64 string"""
        try:
            # Decode base64
            image_data = base64.b64decode(base64_string)
            return await self.process_image_bytes(image_data)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "error": f"Base64 decode error: {str(e)}"
            }

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats"""
        return [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"]

    async def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """Validate image file and get metadata"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.get_supported_formats():
                return {"valid": False, "error": f"Unsupported format: {file_ext}"}
            
            # Try to open image
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                file_size = os.path.getsize(file_path)
                
                # Check image size limits (max 10MB)
                max_size = 10 * 1024 * 1024  # 10MB
                if file_size > max_size:
                    return {
                        "valid": False,
                        "error": f"Image too large: {file_size} bytes (max: {max_size} bytes)"
                    }
                
                # Check dimensions (max 4000x4000)
                max_dimension = 4000
                if width > max_dimension or height > max_dimension:
                    return {
                        "valid": False,
                        "error": f"Image dimensions too large: {width}x{height} (max: {max_dimension}x{max_dimension})"
                    }
                
                return {
                    "valid": True,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "file_size": file_size,
                    "format": file_ext
                }
                
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def extract_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata from image"""
        try:
            with Image.open(image_path) as img:
                # Basic metadata
                metadata = {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "file_size": os.path.getsize(image_path)
                }
                
                # EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    if exif_data:
                        # Extract common EXIF tags
                        metadata["exif"] = {
                            "datetime": exif_data.get(306),  # DateTime
                            "camera_make": exif_data.get(271),  # Make
                            "camera_model": exif_data.get(272),  # Model
                            "orientation": exif_data.get(274),  # Orientation
                        }
                
                # Calculate image complexity (for OCR difficulty estimation)
                metadata["complexity"] = self._calculate_image_complexity(img)
                
                return metadata
                
        except Exception as e:
            print(f"⚠️ Metadata extraction failed: {e}")
            return {}

    def _calculate_image_complexity(self, image: Image.Image) -> Dict[str, float]:
        """Calculate image complexity metrics"""
        try:
            # Convert to numpy array
            img_array = np.array(image.convert('L'))  # Convert to grayscale
            
            # Calculate various complexity metrics
            complexity = {
                "variance": float(np.var(img_array)),
                "edge_density": self._calculate_edge_density(img_array),
                "text_likelihood": self._estimate_text_likelihood(img_array)
            }
            
            return complexity
            
        except:
            return {"variance": 0.0, "edge_density": 0.0, "text_likelihood": 0.0}

    def _calculate_edge_density(self, img_array: np.ndarray) -> float:
        """Calculate edge density using Canny edge detection"""
        try:
            edges = cv2.Canny(img_array, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            return float(edge_density)
        except:
            return 0.0

    def _estimate_text_likelihood(self, img_array: np.ndarray) -> float:
        """Estimate likelihood that image contains text"""
        try:
            # Look for horizontal and vertical lines (text characteristics)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            horizontal_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, vertical_kernel)
            
            h_score = np.sum(horizontal_lines > 0) / horizontal_lines.size
            v_score = np.sum(vertical_lines > 0) / vertical_lines.size
            
            # Text typically has more horizontal structure
            text_likelihood = h_score + (v_score * 0.3)
            return float(min(text_likelihood * 10, 1.0))  # Scale and cap at 1.0
            
        except:
            return 0.0

    async def detect_text_regions(self, image_path: str) -> List[Dict]:
        """Detect text regions in image using EAST text detector"""
        try:
            # This would require OpenCV's EAST text detector
            # For now, return OCR bounding boxes
            result = await self.extract_text_from_image(image_path)
            return result.get("bounding_boxes", [])
            
        except Exception as e:
            print(f"⚠️ Text region detection failed: {e}")
            return []

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
