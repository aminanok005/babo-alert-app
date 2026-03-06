import edge_tts
import asyncio
from pathlib import Path
from gtts import gTTS
import os
import logging

logger = logging.getLogger(__name__)

# Try to import voice cloner (optional dependency)
try:
    from app.utils.islamic_voice import IslamicVoiceCloner
    VOICE_CLONER_AVAILABLE = True
except ImportError:
    VOICE_CLONER_AVAILABLE = False
    logger.warning("IslamicVoiceCloner not available - voice cloning disabled")


async def generate_audio(
    text,
    clip_number,
    output_dir,
    delay_between_clips=2,
    character: str = None,
    character_name: str = None,
    use_voice_clone: bool = False
):
    """Generate TTS audio with optional voice cloning
    
    Args:
        text: Text to convert to speech
        clip_number: Clip number for naming
        output_dir: Output directory
        delay_between_clips: Delay in seconds between clips to avoid rate limiting
        character: Character identifier (e.g., 'sheikh', 'omar', 'aisha')
        character_name: Character display name
        use_voice_clone: Whether to use voice cloning instead of TTS
    """
    voice = "th-TH-PremwadeeNeural"
    output_path = output_dir / f"clip_{clip_number}.mp3"
    
    # Add delay to avoid rate limiting (more delay for higher clip numbers)
    if clip_number > 1 and delay_between_clips > 0:
        await asyncio.sleep(delay_between_clips * (clip_number - 1))
    
    # Try voice cloning first if enabled and available
    if use_voice_clone and VOICE_CLONER_AVAILABLE and character:
        try:
            logger.info(f"Using voice cloning for clip {clip_number} with character: {character}")
            
            with IslamicVoiceCloner() as voice_cloner:
                # Get voice preset for character
                voice_preset = _get_character_voice_preset(character)
                voice_id = voice_preset.get("voice_id")
                
                # If no cloned voice ID, use voice settings with ElevenLabs
                if voice_id:
                    from app.utils.islamic_voice import VoiceSettings
                    voice_settings = VoiceSettings(
                        stability=voice_preset.get("stability", 0.75),
                        similarity_boost=voice_preset.get("similarity_boost", 0.85),
                        style=voice_preset.get("style", 0.35)
                    )
                    result = await voice_cloner.generate_tts(
                        text=text,
                        voice_id=voice_id,
                        output_path=str(output_path),
                        voice_settings=voice_settings
                    )
                else:
                    # No voice ID configured - use fallback TTS (Edge/gTTS)
                    # This is intentional when voice_id is None
                    logger.info(f"No cloned voice ID for character '{character}', using fallback TTS")
                    result = None
                
                if result and result.success:
                    logger.info(f"Voice generation succeeded for clip {clip_number}")
                    return str(output_path)
                else:
                    logger.warning(f"Voice cloning not available or failed, falling back to TTS")
        except Exception as e:
            logger.warning(f"Voice cloning error: {e}, falling back to TTS")
    
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


def _get_character_voice_preset(character: str) -> dict:
    """Get voice preset configuration for a character"""
    presets = {
        "sheikh": {
            "name": "Sheikh Ahmad Al-Thai",
            "voice_id": None,  # Would be set after voice cloning
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.35
        },
        "omar": {
            "name": "Omar Young Muslim",
            "voice_id": None,
            "stability": 0.65,
            "similarity_boost": 0.80,
            "style": 0.50
        },
        "aisha": {
            "name": "Sister Aisha",
            "voice_id": None,
            "stability": 0.70,
            "similarity_boost": 0.85,
            "style": 0.40
        }
    }
    return presets.get(character, presets["sheikh"])