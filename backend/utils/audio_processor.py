"""
Audio processing module using OpenAI Whisper for speech-to-text
"""
import whisper
import torch
import tempfile
import os
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import librosa
import numpy as np

class AudioProcessor:
    def __init__(self):
        self.model = None
        self.model_size = "base"  # Options: tiny, base, small, medium, large
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def load_model(self):
        """Load Whisper model"""
        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor, 
                whisper.load_model, 
                self.model_size
            )
            print(f"✅ Whisper model '{self.model_size}' loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            raise

    async def transcribe_audio(self, audio_file_path: str, language: str = None) -> Dict[str, Any]:
        """Transcribe audio file to text using Whisper"""
        if not self.model:
            await self.load_model()
        
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                audio_file_path,
                language
            )
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": result["segments"],
                "confidence": self._calculate_confidence(result["segments"]),
                "duration": self._get_audio_duration(audio_file_path)
            }
            
        except Exception as e:
            print(f"❌ Audio transcription failed: {e}")
            return {
                "text": "",
                "language": "unknown",
                "segments": [],
                "confidence": 0.0,
                "duration": 0.0,
                "error": str(e)
            }

    def _transcribe_sync(self, audio_file_path: str, language: str = None) -> Dict:
        """Synchronous transcription method"""
        options = {
            "task": "transcribe",
            "fp16": torch.cuda.is_available()
        }
        
        if language:
            options["language"] = language
        
        return self.model.transcribe(audio_file_path, **options)

    def _calculate_confidence(self, segments: list) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        # Whisper doesn't provide confidence scores directly
        # We'll estimate based on segment characteristics
        total_confidence = 0.0
        for segment in segments:
            # Estimate confidence based on segment properties
            text_length = len(segment.get("text", "").strip())
            duration = segment.get("end", 0) - segment.get("start", 0)
            
            if duration > 0 and text_length > 0:
                # Longer, more coherent segments get higher confidence
                confidence = min(0.95, 0.5 + (text_length / (duration * 10)))
            else:
                confidence = 0.3
            
            total_confidence += confidence
        
        return total_confidence / len(segments)

    def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get audio file duration"""
        try:
            duration = librosa.get_duration(filename=audio_file_path)
            return duration
        except:
            return 0.0

    async def process_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """Process audio from bytes"""
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the temporary file
            result = await self.transcribe_audio(temp_file_path)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def convert_audio_format(self, input_path: str, output_path: str = None) -> str:
        """Convert audio to WAV format for better compatibility"""
        try:
            # Load audio with librosa (supports many formats)
            audio_data, sample_rate = librosa.load(input_path, sr=16000)  # Whisper prefers 16kHz
            
            if output_path is None:
                output_path = input_path.rsplit('.', 1)[0] + '_converted.wav'
            
            # Save as WAV
            import soundfile as sf
            sf.write(output_path, audio_data, sample_rate)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Audio conversion failed: {e}")
            return input_path  # Return original if conversion fails

    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return [
            ".wav", ".mp3", ".m4a", ".flac", ".aac", 
            ".ogg", ".wma", ".mp4", ".mov", ".avi"
        ]

    async def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file and get metadata"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.get_supported_formats():
                return {"valid": False, "error": f"Unsupported format: {file_ext}"}
            
            # Get audio metadata
            duration = self._get_audio_duration(file_path)
            file_size = os.path.getsize(file_path)
            
            # Check duration limits (max 30 minutes for free tier)
            max_duration = 30 * 60  # 30 minutes
            if duration > max_duration:
                return {
                    "valid": False, 
                    "error": f"Audio too long: {duration:.1f}s (max: {max_duration}s)"
                }
            
            return {
                "valid": True,
                "duration": duration,
                "file_size": file_size,
                "format": file_ext
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def extract_audio_features(self, audio_file_path: str) -> Dict[str, Any]:
        """Extract additional audio features for analysis"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_file_path)
            
            # Extract features
            features = {
                "duration": len(audio_data) / sample_rate,
                "sample_rate": sample_rate,
                "rms_energy": float(np.sqrt(np.mean(audio_data**2))),
                "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(audio_data))),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(audio_data, sr=sample_rate))),
                "tempo": float(librosa.beat.tempo(audio_data, sr=sample_rate)[0])
            }
            
            # Estimate speech characteristics
            features["speech_rate"] = self._estimate_speech_rate(audio_data, sample_rate)
            features["silence_ratio"] = self._estimate_silence_ratio(audio_data)
            
            return features
            
        except Exception as e:
            print(f"⚠️ Feature extraction failed: {e}")
            return {}

    def _estimate_speech_rate(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Estimate speech rate (words per minute)"""
        try:
            # Simple estimation based on energy peaks
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.01 * sample_rate)     # 10ms hop
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Find speech segments (above threshold)
            threshold = np.mean(rms) * 0.3
            speech_frames = rms > threshold
            
            # Estimate syllables/words from energy peaks
            diff = np.diff(speech_frames.astype(int))
            speech_segments = np.sum(diff == 1)  # Number of speech onsets
            
            duration_minutes = len(audio_data) / sample_rate / 60
            estimated_wpm = (speech_segments * 2) / duration_minutes if duration_minutes > 0 else 0
            
            return min(estimated_wpm, 300)  # Cap at reasonable maximum
            
        except:
            return 0.0

    def _estimate_silence_ratio(self, audio_data: np.ndarray) -> float:
        """Estimate ratio of silence in audio"""
        try:
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_data**2))
            threshold = rms * 0.1
            
            # Count silent samples
            silent_samples = np.sum(np.abs(audio_data) < threshold)
            silence_ratio = silent_samples / len(audio_data)
            
            return float(silence_ratio)
            
        except:
            return 0.0

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
