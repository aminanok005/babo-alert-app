#!/bin/bash
# Render Video Script for n8n Workflow
# Usage: ./render_clip.sh <clip_number> <text> <output_path>

CLIP_NUM=$1
TEXT=$2
OUTPUT_PATH=$3

# Get environment variables
source .env 2>/dev/null

# Font path - try multiple locations
FONT_PATHS=(
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf"
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    "/usr/share/fonts/TTF/DejaVuSans.ttf"
)

FONT_PATH=""
for fp in "${FONT_PATHS[@]}"; do
    if [ -f "$fp" ]; then
        FONT_PATH="$fp"
        break
    fi
done

if [ -z "$FONT_PATH" ]; then
    echo "Warning: No Thai font found, using default"
    FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
fi

# Input files
AUDIO_PATH="/tmp/clip_${CLIP_NUM}.mp3"

# Get audio duration
AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO_PATH" 2>/dev/null)
if [ -z "$AUDIO_DURATION" ]; then
    AUDIO_DURATION=30
fi

echo "Audio duration: $AUDIO_DURATION seconds"

# Escape text for FFmpeg
TEXT_ESCAPED=$(echo "$TEXT" | sed "s/'/\\\\'/g" | cut -c1-200)

# Render video with text overlay and fade effects
# Use audio duration for video length
ffmpeg -y \
    -f lavfi -i "color=c=black:s=1080x1920:d=${AUDIO_DURATION}" \
    -i "$AUDIO_PATH" \
    -vf "drawtext=text='${TEXT_ESCAPED}':fontfile=${FONT_PATH}:fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h-120:box=1:boxcolor=black@0.5:boxborderw=15" \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 128k \
    -shortest \
    "$OUTPUT_PATH" 2>&1

if [ $? -eq 0 ]; then
    echo "Success: $OUTPUT_PATH"
else
    echo "Error: Failed to render video"
    exit 1
fi
