import edge_tts
import asyncio
from pathlib import Path

async def generate_audio(text, clip_number, output_dir):
    voice = "th-TH-PremwadeeNeural"
    output_path = output_dir / f"clip_{clip_number}.mp3"
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    
    return str(output_path)