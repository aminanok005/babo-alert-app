"""
Islamic Avatar Generator
AI Avatar System for Islamic Content using HeyGen API
"""

import os
import asyncio
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class AvatarConfig:
    """Configuration for Avatar generation"""
    quality: str = "high"
    language: str = "th-TH"
    aspect_ratio: str = "9:16"
    callback_url: Optional[str] = None


@dataclass
class AvatarStatus(str, Enum):
    """Status of avatar operation"""
    SUCCESS = "success"
    FALLBACK = "fallback"
    ERROR = "error"


@dataclass
class AvatarResult:
    """Result from Avatar generation"""
    video_id: str
    video_url: str
    status: str
    duration: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if operation was successful"""
        return self.status == AvatarStatus.SUCCESS


@dataclass
class AvatarOperationResult:
    """Result wrapper that explicitly indicates operation status"""
    success: bool
    status: AvatarStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    @property
    def is_fallback(self) -> bool:
        """Check if operation used fallback mode"""
        return self.status == AvatarStatus.FALLBACK
    
    @property
    def is_error(self) -> bool:
        """Check if operation failed with error"""
        return self.status == AvatarStatus.ERROR


class IslamicAvatarGenerator:
    """
    ระบบสร้าง AI Avatar สำหรับเนื้อหาอิสลาม
    
    Features:
    - Photo-based Avatar creation
    - Video generation from scripts
    - Voice synchronization
    - Multi-language support (Thai, Arabic, English)
    """
    
    def __init__(self, config: Optional[AvatarConfig] = None):
        self.heygen_api_key = os.getenv("HEYGEN_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.heygen.com/v1"
        self.config = config or AvatarConfig()
        self._api_configured = bool(self.heygen_api_key)
        
        # Session for connection pooling
        self.session = requests.Session()
        if self.heygen_api_key:
            self.session.headers.update({"X-API-KEY": self.heygen_api_key})
    
    def close(self):
        """Close the HTTP session to prevent resource leaks"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _check_api_keys(self) -> bool:
        """Check if API keys are configured"""
        if not self.heygen_api_key:
            logger.warning("HEYGEN_API_KEY not configured - using fallback mode")
            return False
        return True
    
    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return self._api_configured
    
    async def create_photo_based_avatar(
        self,
        image_path: str,
        avatar_name: str,
        voice_id: Optional[str] = None,
        visibility: str = "private"
    ) -> AvatarOperationResult:
        """
        สร้าง Avatar จากภาพถ่าย (Photo-based Digital Twin)
        
        Args:
            image_path: เส้นทางไฟล์รูปภาพ
            avatar_name: ชื่อ Avatar (เช่น "Sheikh Ahmad", "Islamic Scholar")
            voice_id: ID ของเสียงที่ต้องการใช้
            visibility: public หรือ private
            
        Returns:
            AvatarOperationResult: Result with explicit success/fallback/error status
        """
        # Validate inputs
        if not image_path:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message="image_path is required"
            )
        
        if not avatar_name:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message="avatar_name is required"
            )
        
        # Validate file exists
        if not os.path.exists(image_path):
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Image file not found: {image_path}"
            )
        
        if not self._check_api_keys():
            fallback = self._create_fallback_avatar(image_path, avatar_name)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data=fallback,
                error_message="Using fallback mode - HeyGen API not configured"
            )
        
        # Validate file size
        try:
            file_size = os.path.getsize(image_path)
        except OSError as e:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Cannot read file: {e}"
            )
            
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
            fallback = self._create_fallback_avatar(image_path, avatar_name)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data=fallback,
                error_message="File too large, using fallback mode"
            )
        
        try:
            # 1. Upload image to HeyGen
            avatar_data = {
                "avatar_name": avatar_name,
                "avatar_type": "photo",
                "visibility": visibility
            }
            
            # Upload image file
            with open(image_path, 'rb') as img_file:
                files = {'file': img_file}
                response = self.session.post(
                    f"{self.base_url}/avatar",
                    data=avatar_data,
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                return AvatarOperationResult(
                    success=True,
                    status=AvatarStatus.SUCCESS,
                    data=response.json()
                )
            else:
                logger.warning(f"HeyGen API error: {response.status_code}")
                fallback = self._create_fallback_avatar(image_path, avatar_name)
                return AvatarOperationResult(
                    success=True,
                    status=AvatarStatus.FALLBACK,
                    data=fallback,
                    error_message=f"API returned status {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error creating avatar: {e}")
            fallback = self._create_fallback_avatar(image_path, avatar_name)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data=fallback,
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error creating avatar: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    def _create_fallback_avatar(
        self,
        image_path: str,
        avatar_name: str
    ) -> Dict[str, Any]:
        """Fallback method when HeyGen is not available"""
        return {
            "avatar_id": f"fallback_{avatar_name.lower().replace(' ', '_')}",
            "avatar_name": avatar_name,
            "status": "fallback_mode",
            "image_path": image_path,
            "message": "Running in fallback mode - use FFmpeg renderer"
        }
    
    async def generate_talking_avatar_video(
        self,
        avatar_id: str,
        script_text: str,
        language: str = "th-TH",
        voice_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> AvatarOperationResult:
        """
        สร้างวิดีโอ Avatar พูดตามสคริปต์
        
        Args:
            avatar_id: ID ของ Avatar
            script_text: ข้อความสคริปต์
            language: ภาษา (th-TH, en-US, ar-SA)
            voice_id: ID เสียง (ถ้าไม่ใช้ default ของ avatar)
            title: หัวข้อวิดีโอ
            
        Returns:
            AvatarOperationResult: Result with explicit success/fallback/error status
        """
        # Validate inputs
        if not avatar_id:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message="avatar_id is required"
            )
        
        if not script_text:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message="script_text is required"
            )
        
        if not self._check_api_keys() or avatar_id.startswith("fallback_"):
            fallback = self._create_fallback_video(script_text, language)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data={
                    "video_id": fallback.video_id,
                    "video_url": fallback.video_url,
                    "status": fallback.status
                },
                error_message="Using fallback mode - HeyGen API not configured"
            )
        
        try:
            video_payload = {
                "script": {
                    "type": "text",
                    "input": script_text,
                    "provider": {
                        "type": "heygen",
                        "voice_id": voice_id or "default"
                    }
                },
                "caption": False,
                "dimensions": {
                    "width": 720,
                    "height": 1280
                },
                "test": False,
                "callback_id": f"islamic_video_{int(time.time())}"
            }
            
            if title:
                video_payload["title"] = title
            
            response = self.session.post(
                f"{self.base_url}/video/generation",
                json=video_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                video_id = data.get("data", {}).get("video_id")
                
                if video_id:
                    # Wait for video to be ready
                    video_url = await self._wait_for_video(video_id)
                    return AvatarOperationResult(
                        success=True,
                        status=AvatarStatus.SUCCESS,
                        data={
                            "video_id": video_id,
                            "video_url": video_url,
                            "status": "completed"
                        }
                    )
            
            # Fallback if generation fails
            fallback = self._create_fallback_video(script_text, language)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data={
                    "video_id": fallback.video_id,
                    "video_url": fallback.video_url,
                    "status": fallback.status
                },
                error_message=f"API returned status {response.status_code}"
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error generating video: {e}")
            fallback = self._create_fallback_video(script_text, language)
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data={
                    "video_id": fallback.video_id,
                    "video_url": fallback.video_url,
                    "status": fallback.status
                },
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error generating video: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    def _create_fallback_video(
        self,
        script_text: str,
        language: str
    ) -> AvatarResult:
        """Create fallback video info"""
        return AvatarResult(
            video_id=f"fallback_{int(time.time())}",
            video_url="",
            status="fallback",
            message="Use FFmpeg renderer instead"
        )
    
    async def _wait_for_video(
        self,
        video_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> str:
        """
        รอให้ video render เสร็จ
        
        Args:
            video_id: ID ของวิดีโอ
            timeout: เวลาสูงสุดในการรอ (วินาที)
            poll_interval: ช่วงเวลาในการตรวจสอบ
            
        Returns:
            str: URL ของวิดีโอ
            
        Raises:
            TimeoutError: เมื่อหมดเวลารอ
            requests.RequestException: เมื่อเกิด network error
        """
        start_time = time.time()
        last_error = None
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.base_url}/video/generation/{video_id}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("data", {}).get("status")
                    
                    if status == "completed":
                        return data.get("data", {}).get("video_url", "")
                    elif status == "failed":
                        error_msg = data.get("data", {}).get("error", "Video generation failed")
                        raise Exception(f"Video generation failed: {error_msg}")
                elif response.status_code >= 500:
                    # Server error - continue polling
                    last_error = f"Server error: {response.status_code}"
                else:
                    # Client error - don't retry
                    raise requests.HTTPError(f"Client error: {response.status_code}")
                
                await asyncio.sleep(poll_interval)
                
            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Video generation timeout after {timeout}s. Last error: {last_error}")
    
    async def generate_video_batch(
        self,
        avatar_id: str,
        scripts: List[Dict[str, str]],
        language: str = "th-TH",
        voice_id: Optional[str] = None
    ) -> List[AvatarResult]:
        """
        สร้างวิดีโอหลายคลิปพร้อมกัน
        
        Args:
            avatar_id: ID ของ Avatar
            scripts: List of {"text": "...", "title": "..."}
            language: ภาษา
            voice_id: ID เสียง
            
        Returns:
            List[AvatarResult]: รายการวิดีโอที่สร้าง
        """
        results = []
        
        for i, script in enumerate(scripts):
            logger.info(f"🎬 Generating clip {i+1}/{len(scripts)}...")
            
            result = await self.generate_talking_avatar_video(
                avatar_id=avatar_id,
                script_text=script["text"],
                language=language,
                voice_id=voice_id,
                title=script.get("title", f"Clip {i+1}")
            )
            
            results.append(result)
            
            # Rate limiting
            if i < len(scripts) - 1:
                await asyncio.sleep(2)
        
        return results
    
    def get_avatar_list(self) -> AvatarOperationResult:
        """ดึงรายการ Avatars ทั้งหมด"""
        if not self._check_api_keys():
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data=[],
                error_message="Using fallback mode - HeyGen API not configured"
            )
        
        try:
            response = self.session.get(
                f"{self.base_url}/avatars",
                timeout=30
            )
            
            if response.status_code == 200:
                return AvatarOperationResult(
                    success=True,
                    status=AvatarStatus.SUCCESS,
                    data=response.json().get("data", [])
                )
            else:
                return AvatarOperationResult(
                    success=False,
                    status=AvatarStatus.ERROR,
                    error_message=f"API returned status {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error fetching avatars: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error fetching avatars: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )
    
    async def delete_avatar(self, avatar_id: str) -> AvatarOperationResult:
        """ลบ Avatar"""
        # Validate input
        if not avatar_id:
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message="avatar_id is required"
            )
        
        if not self._check_api_keys():
            return AvatarOperationResult(
                success=True,
                status=AvatarStatus.FALLBACK,
                data={"deleted": False},
                error_message="Using fallback mode - HeyGen API not configured"
            )
        
        try:
            response = self.session.delete(
                f"{self.base_url}/avatar/{avatar_id}",
                timeout=30
            )
            if response.status_code == 200:
                return AvatarOperationResult(
                    success=True,
                    status=AvatarStatus.SUCCESS,
                    data={"deleted": True}
                )
            else:
                return AvatarOperationResult(
                    success=False,
                    status=AvatarStatus.ERROR,
                    error_message=f"API returned status {response.status_code}"
                )
        except requests.RequestException as e:
            logger.error(f"Network error deleting avatar: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Network error: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error deleting avatar: {e}")
            return AvatarOperationResult(
                success=False,
                status=AvatarStatus.ERROR,
                error_message=f"Unexpected error: {e}"
            )


class AvatarRenderer:
    """
    Fallback renderer เมื่อไม่ใช้ HeyGen
    ใช้ FFmpeg + TTS สำหรับสร้างวิดีโอ
    """
    
    def __init__(self):
        self.assets_dir = Path("assets")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def render_with_static_image(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        text_overlay: Optional[str] = None
    ) -> str:
        """
        Render วิดีโอด้วยรูปภาพนิ่ง + เสียง
        
        Args:
            image_path: รูปภาพ Background
            audio_path: ไฟล์เสียง
            output_path: เส้นทางไฟล์ Output
            text_overlay: ข้อความที่แสดง
            
        Returns:
            str: เส้นทางไฟล์วิดีโอ
        """
        import subprocess
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        if text_overlay:
            # Add text overlay
            cmd.insert(6, "-vf")
            cmd.insert(7, f"drawtext=text='{text_overlay}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h-100:borderw=2:bordercolor=black")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e}")
            raise


# ============= Factory Function =============

def create_avatar_generator(
    quality: str = "high",
    language: str = "th-TH"
) -> IslamicAvatarGenerator:
    """Factory function สำหรับสร้าง Avatar Generator"""
    config = AvatarConfig(
        quality=quality,
        language=language
    )
    return IslamicAvatarGenerator(config)


# ============= Example Usage =============

async def main():
    """ตัวอย่างการใช้งาน"""
    
    # สร้าง Avatar Generator
    generator = IslamicAvatarGenerator()
    
    # ตัวอย่าง: สร้างวิดีโอจากสคริปต์
    script = """
    พี่น้องผู้ศรัทธาที่เคารพทุกท่าน
    
    วันนี้เราจะมาพูดถึงความเมตตาของอัลลอฮฺ ซ.บ.
    ที่ทรงประทานแก่เราทุกคน
    
    จงจำไว้ว่า ท่านนบี ﷺ กล่าวว่า...
    """
    
    # สร้างวิดีโอ (ถ้ามี API Key)
    # result = await generator.generate_talking_avatar_video(
    #     avatar_id="your_avatar_id",
    #     script_text=script,
    #     language="th-TH"
    # )
    # print(f"Video URL: {result.video_url}")
    
    print("✅ Islamic Avatar Generator initialized")


if __name__ == "__main__":
    asyncio.run(main())
