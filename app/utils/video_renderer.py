import asyncio
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import avatar generator (optional dependency)
try:
    from app.utils.islamic_avatar import IslamicAvatarGenerator
    AVATAR_GENERATOR_AVAILABLE = True
except ImportError:
    AVATAR_GENERATOR_AVAILABLE = False
    logger.warning("IslamicAvatarGenerator not available - avatar generation disabled")


async def render_video(
    audio_path,
    text,
    clip_number,
    output_dir,
    character: str = None,
    character_name: str = None,
    use_avatar: bool = False
):
    """Render video from audio and text using ffmpeg
    
    Args:
        audio_path: Path to audio file
        text: Text overlay for the video
        clip_number: Clip number for naming
        output_dir: Output directory
        character: Character identifier (e.g., 'sheikh', 'omar', 'aisha')
        character_name: Character display name
        use_avatar: Whether to generate AI avatar video
    """
    output_path = output_dir / f"clip_{clip_number}.mp4"
    
    # Try avatar generation first if enabled and available
    if use_avatar and AVATAR_GENERATOR_AVAILABLE and character:
        try:
            logger.info(f"Using avatar for clip {clip_number} with character: {character}")
            
            with IslamicAvatarGenerator() as avatar_gen:
                # Generate avatar video
                result = await avatar_gen.generate_talking_avatar_video(
                    avatar_id=_get_character_avatar_id(character),
                    script_text=text,
                    language="th-TH",
                    title=f"Clip {clip_number}"
                )
                
                if result.success:
                    logger.info(f"Avatar generation succeeded for clip {clip_number}")
                    # If avatar succeeded but doesn't have video path, use fallback
                    if result.data and result.data.get("video_url"):
                        # Download and return the avatar video
                        return await _download_avatar_video(result.data["video_url"], str(output_path))
                    return str(output_path)
                else:
                    logger.warning(f"Avatar generation failed: {result.error_message}, using fallback")
        except Exception as e:
            logger.warning(f"Avatar generation error: {e}, using fallback")
    
    # Fallback: Create video with text overlay (original implementation)
    return await _render_fallback_video(audio_path, text, clip_number, output_dir)


async def _download_avatar_video(video_url: str, output_path: str) -> str:
    """Download avatar video from URL"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as response:
            if response.status == 200:
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                return output_path
    raise Exception(f"Failed to download avatar video from {video_url}")


def _get_character_avatar_id(character: str) -> str:
    """Get avatar ID for a character"""
    avatar_ids = {
        "sheikh": "avatar_sheikh_001",
        "omar": "avatar_omar_001",
        "aisha": "avatar_aisha_001"
    }
    return avatar_ids.get(character, avatar_ids["sheikh"])


async def _render_fallback_video(audio_path, text, clip_number, output_dir):
    """Original fallback video rendering with text overlay"""
    font_paths = [
        "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    
    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            break
    
    if font_path is None:
        # Fallback - create video without text overlay
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=10",
            "-i", audio_path,
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            str(output_path)
        ]
    else:
        # Truncate text for display (first 100 chars)
        display_text = text[:100].replace("'", "\\'").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d=30",
            "-i", audio_path,
            "-vf", f"drawtext=text='{display_text}':fontfile={font_path}:fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=10",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(output_path)
        ]
    
    # Use asyncio subprocess
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown error"
        raise Exception(f"FFmpeg error: {error_msg}")
    
    return str(output_path)
