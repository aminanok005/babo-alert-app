"""
Islamic Voice Cloning System
ระบบ Voice Cloning สำหรับเนื้อหาอิสลาม
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Language code mapping for gTTS
GTTS_LANGUAGE_MAP = {
    'th-TH': 'th',
    'ar-SA': 'ar',
    'en-US': 'en',
    'en-GB': 'en',
    'ms-MY': 'ms',
    'id-ID': 'id',
}


@dataclass
class VoiceOperationResult:
    """Result wrapper that explicitly indicates operation status"""
    success: bool
    status: VoiceStatus
    data: Optional[Any] = None
    error_message: Optional[str] = None
    
    @property
    def is_fallback(self) -> bool:
        """Check if operation used fallback mode"""
        return self.status == VoiceStatus.FALLBACK
    
    @property
    def is_error(self) -> bool:
        """Check if operation failed with error"""
        return self.status == VoiceStatus.ERROR


class VoiceStatus(str, Enum):
    """Status of voice operation"""
    SUCCESS = "success"
    FALLBACK = "fallback"
    ERROR = "error"


@dataclass
class VoiceSettings:
    """การตั้งค่าเสียง"""
    stability: float = 0.75
    similarity_boost: float = 0.85
    style: float = 0.35
    use_speaker_boost: bool = True


@dataclass
class VoicePreset:
    """Preset เสียงสำหรับเนื้อหาอิสลาม"""
    name: str
    description: str
    settings: VoiceSettings
    recommended_for: List[str] = field(default_factory=list)


class IslamicVoiceCloner:
    """
    ระบบ Clone เสียงสำหรับเนื้อหาอิสลาม
    
    Features:
    - Voice Cloning จากไฟล์เสียงตัวอย่าง
    - TTS สำหรับภาษาไทยและอาหรับ
    - Voice Presets สำหรับตัวละครต่างๆ
    - ElevenLabs API Integration
    """
    
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.heygen_api_key = os.getenv("HEYGEN_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self._api_configured = bool(self.elevenlabs_api_key)
        
        # Session for connection pooling
        self.session = requests.Session()
        if self.elevenlabs_api_key:
            self.session.headers.update({
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            })
        
        # Initialize voice presets
        self._init_voice_presets()
    
    def close(self):
        """Close the HTTP session to prevent resource leaks"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return self._api_configured
    
    def _init_voice_presets(self):
        """กำหนด Voice Presets"""
        self.voice_presets = {
            "scholar_deep": VoicePreset(
                name="scholar_deep",
                description="เสียงนักวิชาการลึกซึ้ง น่าเกรงขาม",
                settings=VoiceSettings(
                    stability=0.75,
                    similarity_boost=0.85,
                    style=0.35,
                    use_speaker_boost=True
                ),
                recommended_for=["Quran", "Hadith", "Warnings", "Tafsir"]
            ),
            "youth_energetic": VoicePreset(
                name="youth_energetic",
                description="เสียงเยาวชน กระตือรือร้น",
                settings=VoiceSettings(
                    stability=0.50,
                    similarity_boost=0.75,
                    style=0.65,
                    use_speaker_boost=False
                ),
                recommended_for=["Lifestyle", "Dawah", "Youth"]
            ),
            "gentle_reminder": VoicePreset(
                name="gentle_reminder",
                description="เสียงอ่อนโยน สำหรับเตือนใจ",
                settings=VoiceSettings(
                    stability=0.80,
                    similarity_boost=0.70,
                    style=0.25,
                    use_speaker_boost=True
                ),
                recommended_for=["Reminders", "Duas", "Encouragement"]
            ),
            "sister_soft": VoicePreset(
                name="sister_soft",
                description="เสียงนุ่มนวล อ่อนโยน",
                settings=VoiceSettings(
                    stability=0.80,
                    similarity_boost=0.75,
                    style=0.20,
                    use_speaker_boost=True
                ),
                recommended_for=["Women", "Family", "Children"]
            ),
            "elder_warm": VoicePreset(
                name="elder_warm",
                description="เสียงอบอุ่น ประสบการณ์",
                settings=VoiceSettings(
                    stability=0.85,
                    similarity_boost=0.80,
                    style=0.15,
                    use_speaker_boost=True
                ),
                recommended_for=["Advice", "Wisdom", "Stories"]
            )
        }
        
        # Built-in voices from ElevenLabs
        self.builtin_voices = {
            "rachel": "21m00Tcm4TlvDq8ikWAM",      # Female
            "drew": "2bD62pL4P2O3nI9jy0cJ",        # Male
            "clyde": "2eTWA46Kzq3nI9jy0cK5",       # Male
            "jennifer": "CGmS69TkY6P5K3kI9jym",    # Female
            "adam": "pNInz6obpgDQGcFmaJgB"        # Male
        }
    
    def _check_api_key(self) -> bool:
        """ตรวจสอบ API Key"""
        if not self.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY not configured - using fallback mode")
            return False
        return True
    
    async def clone_voice_from_sample(
        self,
        voice_name: str,
        sample_audio_path: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> VoiceOperationResult:
        """
        Clone เสียงจากไฟล์ตัวอย่าง
        
        Args:
            voice_name: ชื่อเสียง
            sample_audio_path: ไฟล์เสียงตัวอย่าง (1-2 นาที)
            description: คำอธิบาย
            labels: Labels สำหรับ categorizing
            
        Returns:
            VoiceOperationResult: Result with explicit success/fallback/error status
        """
        # Validate inputs
        if not voice_name:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="voice_name is required"
            )
        
        if not sample_audio_path:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="sample_audio_path is required"
            )
        
        if not self._check_api_key():
            fallback_id = self._create_fallback_voice(voice_name)
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"voice_id": fallback_id},
                error_message="Using fallback mode - ElevenLabs API not configured"
            )
        
        # Validate file exists
        if not os.path.exists(sample_audio_path):
            logger.warning(f"Audio file not found: {sample_audio_path}")
            fallback_id = self._create_fallback_voice(voice_name)
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"voice_id": fallback_id},
                error_message=f"Audio file not found: {sample_audio_path}"
            )
        
        # Validate file size
        try:
            file_size = os.path.getsize(sample_audio_path)
        except OSError as e:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Cannot read file: {e}"
            )
            
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
            fallback_id = self._create_fallback_voice(voice_name)
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"voice_id": fallback_id},
                error_message="File too large, using fallback mode"
            )
        
        try:
            # Prepare data
            data = {
                "name": voice_name,
                "description": description or f"Islamic voice: {voice_name}",
                "labels": labels or {
                    "accent": "arabic",
                    "age": "middle_aged",
                    "gender": "male"
                }
            }
            
            # Upload audio file
            with open(sample_audio_path, 'rb') as audio_file:
                files = {"files": (os.path.basename(sample_audio_path), audio_file, "audio/mpeg")}
                
                response = self.session.post(
                    f"{self.base_url}/voices/add",
                    data=data,
                    files=files,
                    timeout=120
                )
            
            if response.status_code == 200:
                result = response.json()
                voice_id = result.get("voice_id")
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.SUCCESS,
                    data={"voice_id": voice_id}
                )
            else:
                logger.warning(f"Voice cloning failed: {response.status_code}")
                fallback_id = self._create_fallback_voice(voice_name)
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.FALLBACK,
                    data={"voice_id": fallback_id},
                    error_message=f"API returned status {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error cloning voice: {e}")
            fallback_id = self._create_fallback_voice(voice_name)
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"voice_id": fallback_id},
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error cloning voice: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    def _create_fallback_voice(self, voice_name: str) -> str:
        """สร้าง fallback voice ID"""
        return f"fallback_{voice_name.lower().replace(' ', '_')}"
    
    async def generate_tts(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        model_id: str = "eleven_multilingual_v2",
        voice_settings: Optional[VoiceSettings] = None
    ) -> VoiceOperationResult:
        """
        สร้างเสียง TTS จากข้อความ
        
        Args:
            text: ข้อความที่จะพูด
            voice_id: ID ของเสียง
            output_path: เส้นทางไฟล์ Output
            model_id: โมเดลที่ใช้
            voice_settings: การตั้งค่าเสียง
            
        Returns:
            VoiceOperationResult: Result with explicit success/fallback/error status
        """
        # Validate inputs
        if not text:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="text is required"
            )
        
        if not output_path:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="output_path is required"
            )
        
        if not self._check_api_key() or (voice_id and voice_id.startswith("fallback_")):
            fallback_path = await self._generate_fallback_tts(text, output_path)
            if fallback_path:
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.FALLBACK,
                    data={"audio_path": fallback_path},
                    error_message="Using fallback mode - ElevenLabs API not configured"
                )
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="Fallback TTS also failed"
            )
        
        # Validate voice_id
        if not voice_id:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="voice_id is required"
            )
        
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            # Use provided settings or default
            settings = voice_settings or VoiceSettings()
            
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": settings.stability,
                    "similarity_boost": settings.similarity_boost,
                    "style": settings.style,
                    "use_speaker_boost": settings.use_speaker_boost
                }
            }
            
            response = self.session.post(url, json=data, timeout=60)
            
            if response.status_code == 200:
                # Save audio file
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path_obj, 'wb') as f:
                    f.write(response.content)
                
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.SUCCESS,
                    data={"audio_path": str(output_path_obj)}
                )
            else:
                logger.warning(f"TTS generation failed: {response.status_code}")
                fallback_path = await self._generate_fallback_tts(text, output_path)
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.FALLBACK,
                    data={"audio_path": fallback_path},
                    error_message=f"API returned status {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error generating TTS: {e}")
            fallback_path = await self._generate_fallback_tts(text, output_path)
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"audio_path": fallback_path},
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error generating TTS: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    async def _generate_fallback_tts(
        self,
        text: str,
        output_path: str,
        language: str = "th-TH"
    ) -> Optional[str]:
        """Fallback TTS using gTTS"""
        try:
            from gtts import gTTS
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use language mapping for gTTS
            lang_code = GTTS_LANGUAGE_MAP.get(language, 'th')
            tts = gTTS(text=text, lang=lang_code)
            tts.save(str(output_path))
            
            return str(output_path)
        except ImportError:
            logger.warning("gTTS not installed, fallback TTS unavailable")
            return None
        except Exception as e:
            logger.error(f"Fallback TTS failed: {e}")
            return None
    
    def get_preset(self, preset_name: str) -> Optional[VoicePreset]:
        """ดึง Voice Preset"""
        return self.voice_presets.get(preset_name)
    
    def get_preset_for_content(self, content_type: str) -> VoicePreset:
        """ดึง Preset ที่เหมาะสมกับประเภทเนื้อหา"""
        content_lower = content_type.lower()
        
        # Map content types to presets
        if any(kw in content_lower for kw in ["quran", "hadith", "tafsir", "warning"]):
            return self.voice_presets["scholar_deep"]
        elif any(kw in content_lower for kw in ["youth", "lifestyle", "dawah"]):
            return self.voice_presets["youth_energetic"]
        elif any(kw in content_lower for kw in ["women", "family", "sister"]):
            return self.voice_presets["sister_soft"]
        elif any(kw in content_lower for kw in ["elder", "advice", "wisdom"]):
            return self.voice_presets["elder_warm"]
        
        # Default to gentle reminder
        return self.voice_presets["gentle_reminder"]
    
    def list_voices(self) -> VoiceOperationResult:
        """รายการเสียงทั้งหมด"""
        if not self._check_api_key():
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data=self._list_fallback_voices(),
                error_message="Using fallback mode - ElevenLabs API not configured"
            )
        
        try:
            response = self.session.get(f"{self.base_url}/voices", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                voices = [
                    {
                        "voice_id": v["voice_id"],
                        "name": v["name"],
                        "category": v.get("category", "custom")
                    }
                    for v in data.get("voices", [])
                ]
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.SUCCESS,
                    data=voices
                )
            else:
                return VoiceOperationResult(
                    success=False,
                    status=VoiceStatus.ERROR,
                    error_message=f"API returned status {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error listing voices: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error listing voices: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    def _list_fallback_voices(self) -> List[Dict[str, Any]]:
        """Fallback voice list"""
        return [
            {
                "voice_id": "fallback_default",
                "name": "Default (gTTS)",
                "category": "fallback"
            }
        ]
    
    async def delete_voice(self, voice_id: str) -> VoiceOperationResult:
        """ลบเสียง"""
        # Validate input
        if not voice_id:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="voice_id is required"
            )
        
        if not self._check_api_key() or voice_id.startswith("fallback_"):
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"deleted": False},
                error_message="Using fallback mode - cannot delete fallback voices"
            )
        
        try:
            response = self.session.delete(
                f"{self.base_url}/voices/{voice_id}",
                timeout=30
            )
            if response.status_code == 200:
                return VoiceOperationResult(
                    success=True,
                    status=VoiceStatus.SUCCESS,
                    data={"deleted": True}
                )
            else:
                return VoiceOperationResult(
                    success=False,
                    status=VoiceStatus.ERROR,
                    error_message=f"API returned status {response.status_code}"
                )
        except requests.RequestException as e:
            logger.error(f"Network error deleting voice: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error deleting voice: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    def get_audio_duration(self, audio_path: str) -> VoiceOperationResult:
        """ดึงความยาวของไฟล์เสียง (วินาที)"""
        # Validate input
        if not audio_path:
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message="audio_path is required"
            )
        
        # Validate file exists
        if not os.path.exists(audio_path):
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Audio file not found: {audio_path}"
            )
        
        try:
            import subprocess
            
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", 
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", 
                 audio_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            duration = float(result.stdout.strip())
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.SUCCESS,
                data={"duration": duration}
            )
        except FileNotFoundError:
            logger.warning("ffprobe not found, cannot determine duration")
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"duration": 0.0},
                error_message="ffprobe not available"
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting audio duration: {e}")
            return VoiceOperationResult(
                success=True,
                status=VoiceStatus.FALLBACK,
                data={"duration": 0.0},
                error_message=f"Error reading duration: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error getting audio duration: {e}")
            return VoiceOperationResult(
                success=False,
                status=VoiceStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    async def generate_long_text(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        max_chars_per_chunk: int = 2500
    ) -> Optional[str]:
        """
        สร้างเสียงสำหรับข้อความยาว
        
        สำหรับข้อความที่ยาวเกินข้อจำกัดของ API
        จะแบ่งเป็น chunks แล้วรวมกัน
        
        Args:
            text: ข้อความ
            voice_id: ID เสียง
            output_path: เส้นทางไฟล์ Output
            max_chars_per_chunk: จำนวนตัวอักษรสูงสุดต่อ chunk
            
        Returns:
            str: เส้นทางไฟล์เสียง
        """
        # Split text into chunks
        chunks = self._split_text_into_chunks(text, max_chars_per_chunk)
        
        if len(chunks) == 1:
            # Single chunk - generate directly
            return await self.generate_tts(text, voice_id, output_path)
        
        # Multiple chunks - generate and combine
        output_path = Path(output_path)
        temp_dir = output_path.parent / "temp_chunks"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_files = []
        
        for i, chunk in enumerate(chunks):
            chunk_path = temp_dir / f"chunk_{i}.mp3"
            
            result = await self.generate_tts(
                chunk,
                voice_id,
                str(chunk_path)
            )
            
            if result:
                chunk_files.append(result)
            
            # Rate limiting
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
        
        # Combine chunks
        if chunk_files:
            combined = await self._combine_audio_files(chunk_files, str(output_path))
            
            # Cleanup temp files
            for f in chunk_files:
                try:
                    os.remove(f)
                except OSError as e:
                    print(f"⚠️ Failed to cleanup temp file {f}: {e}")
            
            return combined if combined else chunk_files[0]
        
        return None
    
    def _split_text_into_chunks(self, text: str, max_chars: int) -> List[str]:
        """แบ่งข้อความเป็น chunks"""
        # Split by sentences
        sentences = text.replace("\n", " ").split(".")
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += ("." if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk + ".")
        
        return chunks
    
    async def _combine_audio_files(
        self,
        audio_files: List[str],
        output_path: str
    ) -> Optional[str]:
        """รวมไฟล์เสียงหลายไฟล์เข้าด้วยกัน"""
        try:
            import subprocess
            
            output_path = Path(output_path)
            temp_dir = output_path.parent / "temp_chunks"
            temp_dir.mkdir(exist_ok=True)
            
            # Validate and resolve all paths to prevent path traversal
            temp_dir_resolved = temp_dir.resolve()
            validated_files = []
            
            for audio_file in audio_files:
                abs_path = Path(audio_file).resolve()
                # Check for path traversal
                if not str(abs_path).startswith(str(temp_dir_resolved)):
                    # File is outside temp directory, copy it
                    safe_copy = temp_dir_resolved / abs_path.name
                    import shutil
                    shutil.copy2(abs_path, safe_copy)
                    validated_files.append(str(safe_copy))
                else:
                    validated_files.append(str(abs_path))
            
            # Create file list for FFmpeg
            list_file = temp_dir_resolved / "concat_list.txt"
            
            with open(list_file, 'w') as f:
                for audio_file in validated_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Run FFmpeg to combine
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Cleanup
            list_file.unlink(missing_ok=True)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error combining audio: {e}")
            return audio_files[0] if audio_files else None


# ============= Factory Function =============

def create_voice_cloner() -> IslamicVoiceCloner:
    """Factory function สำหรับสร้าง Voice Cloner"""
    return IslamicVoiceCloner()


# ============= Example Usage =============

async def main():
    """ตัวอย่างการใช้งาน"""
    
    # สร้าง Voice Cloner
    cloner = IslamicVoiceCloner()
    
    # ดึง preset สำหรับเนื้อหา
    preset = cloner.get_preset_for_content("Quran")
    print(f"📢 Voice preset: {preset.name}")
    print(f"   Description: {preset.description}")
    print(f"   Settings: {preset.settings}")
    
    # ตัวอย่าง: สร้างเสียง TTS
    # text = "พี่น้องผู้ศรัทธาที่เคารพ วันนี้เราจะมาพูดถึง..."
    # audio_path = await cloner.generate_tts(
    #     text=text,
    #     voice_id="your_voice_id",
    #     output_path="output/audio.mp3"
    # )
    # print(f"✅ Audio saved to: {audio_path}")


if __name__ == "__main__":
    asyncio.run(main())
