#!/usr/bin/env python3
"""
Standalone test script to test the full 7-clip generation workflow
Usage: python3 test_workflow.py <topic>
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.script_generator import generate_script, split_script
from scripts.save_tts import generate_audio


async def test_tts(clip_num, text, is_hero=False):
    """Test TTS generation"""
    print(f"\n🎙️ Generating TTS for clip {clip_num}...")
    try:
        output = await generate_audio(str(clip_num), text, is_hero)
        print(f"   ✅ TTS saved: {output}")
        return output
    except Exception as e:
        print(f"   ❌ TTS failed: {e}")
        return None


def test_render(clip_num, text):
    """Test video rendering"""
    print(f"\n🎬 Rendering video for clip {clip_num}...")
    try:
        # Escape text for bash
        text_escaped = text.replace("'", "\\'")[:200]
        
        cmd = [
            "bash", "scripts/render_clip.sh",
            str(clip_num),
            text,
            f"output/test_clip_{clip_num}.mp4"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   ✅ Video rendered: output/test_clip_{clip_num}.mp4")
            return True
        else:
            print(f"   ❌ Render failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Render error: {e}")
        return False


async def main():
    if len(sys.argv) < 2:
        topic = "ความเมตตาของอัลลอฮ์"
    else:
        topic = sys.argv[1]
    
    print(f"🚀 Starting 7-Clip Generation Test")
    print(f"   Topic: {topic}")
    
    # Step 1: Generate script
    print("\n📝 Step 1: Generating script from Groq...")
    try:
        script = generate_script(topic)
        print(f"   ✅ Script generated ({len(script)} chars)")
        print(f"   Preview: {script[:200]}...")
    except Exception as e:
        print(f"   ❌ Script generation failed: {e}")
        return
    
    # Step 2: Split into 7 clips
    print("\n✂️ Step 2: Splitting script into 7 clips...")
    clips = split_script(script)
    print(f"   ✅ Created {len(clips)} clips")
    
    # Step 3-4: Generate TTS and render each clip
    for i, clip in enumerate(clips[:7]):
        clip_num = i + 1
        is_hero = clip_num in [1, 7]
        
        # Generate TTS
        tts_path = await test_tts(clip_num, clip["text"], is_hero)
        
        # Render video
        if tts_path:
            test_render(clip_num, clip["text"])
    
    print("\n" + "="*50)
    print("✅ Test complete! Check output/ folder for results")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
