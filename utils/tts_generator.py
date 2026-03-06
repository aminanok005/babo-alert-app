import edge_tts
import asyncio
from pathlib import Path
from gtts import gTTS
import os

async def generate_audio(text, clip_number, output_dir, delay_between_clips=2):
    """Generate TTS audio with fallback from Edge TTS to gTTS
    
    Args:
        text: Text to convert to speech
        clip_number: Clip number for naming
        output_dir: Output directory
        delay_between_clips: Delay in seconds between clips to avoid rate limiting
    """
    voice = "th-TH-PremwadeeNeural"
    output_path = output_dir / f"clip_{clip_number}.mp3"
    
    # Add delay to avoid rate limiting (more delay for higher clip numbers)
    if clip_number > 1 and delay_between_clips > 0:
        await asyncio.sleep(delay_between_clips * (clip_number - 1))
    
    # Try edge-tts first, fall back to gTTS if it fails
    try:
        print(f"Trying Edge TTS for clip {clip_number}...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        print(f"Edge TTS succeeded for clip {clip_number}")
    except Exception as e:
        print(f"Edge TTS failed for clip {clip_number}: {e}")
        print(f"Falling back to gTTS for clip {clip_number}...")
        # Fallback to gTTS
        tts = gTTS(text=text, lang='th', slow=False)
        tts.save(str(output_path))
        print(f"gTTS succeeded for clip {clip_number}")
    
    return str(output_path)