import subprocess
from pathlib import Path

async def render_video(audio_path, text, clip_number, output_dir):
    output_path = output_dir / f"clip_{clip_number}.mp4"
    font_path = "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=10",
        "-i", audio_path,
        "-vf", f"drawtext=text='{text[:50]}...':fontfile={font_path}:fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(output_path)
    ]
    
    subprocess.run(cmd, check=True)
    return str(output_path)