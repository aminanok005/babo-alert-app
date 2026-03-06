#!/usr/bin/env python3
"""
TTS Generator Script for n8n Workflow
Usage: python3 save_tts.py <clip_number> <text> <is_hero>
"""

import sys
import asyncio
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import edge_tts
import requests
from gtts import gTTS


async def generate_edge_tts(audio_path, text, voice="th-TH-PremwadeeNeural"):
    """Generate TTS using Edge TTS (free)"""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(audio_path)
        return audio_path
    except Exception as e:
        print(f"Edge TTS failed: {e}")
        raise


def generate_gtts(audio_path, text, lang="th"):
    """Generate TTS using Google Translate TTS (free)"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(audio_path)
        return audio_path
    except Exception as e:
        print(f"gTTS failed: {e}")
        raise


async def generate_elevenlabs(audio_path, text, api_key):
    """Generate TTS using ElevenLabs API (for hero clips)"""
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        return audio_path
    else:
        raise Exception(f"ElevenLabs error: {response.text}")


async def generate_audio(clip_num, text, is_hero=False, use_elevenlabs=False):
    """Main function to generate audio with multiple fallback options"""
    output_path = f"/tmp/clip_{clip_num}.mp3"
    
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    
    # Try 11Labs for hero clips if requested
    if is_hero and use_elevenlabs and elevenlabs_key:
        try:
            print(f"Trying ElevenLabs for clip {clip_num} (hero clip)")
            await generate_elevenlabs(output_path, text, elevenlabs_key)
            return output_path
        except Exception as e:
            print(f"ElevenLabs failed: {e}")
    
    # Try Edge TTS first
    try:
        print(f"Trying Edge TTS for clip {clip_num}")
        await generate_edge_tts(output_path, text)
        return output_path
    except Exception as e:
        print(f"Edge TTS failed: {e}")
    
    # Fallback to gTTS
    try:
        print(f"Trying gTTS (Google) for clip {clip_num}")
        generate_gtts(output_path, text)
        return output_path
    except Exception as e:
        print(f"gTTS failed: {e}")
        raise Exception("All TTS options failed")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 save_tts.py <clip_number> <text> [is_hero]")
        sys.exit(1)
    
    clip_num = sys.argv[1]
    text = sys.argv[2]
    is_hero = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    # Truncate text if too long
    if len(text) > 5000:
        text = text[:5000]
    
    output = asyncio.run(generate_audio(clip_num, text, is_hero))
    print(output)
