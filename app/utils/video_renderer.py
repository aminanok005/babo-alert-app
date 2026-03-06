import asyncio
import os
from pathlib import Path

async def render_video(audio_path, text, clip_number, output_dir):
    """Render video from audio and text using ffmpeg"""
    output_path = output_dir / f"clip_{clip_number}.mp4"
    
    # Find available font
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
