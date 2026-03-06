import edge_tts
import asyncio
from pathlib import Path
from gtts import gTTS
import os

async def generate_audio(text, clip_number, output_dir):
    voice = "th-TH-PremwadeeNeural"
    output_path = output_dir / f"clip_{clip_number}.mp3"
    
    # Try edge-tts first, fall back to gTTS if it fails
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
    except Exception as e:
        # Fallback to gTTS if edge-tts fails
        print(f"edge-tts failed: {e}, trying gTTS...")
        tts = gTTS(text=text, lang='th')
        tts.save(str(output_path))
    
    return str(output_path)