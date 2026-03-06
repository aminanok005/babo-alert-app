#!/bin/bash
# Build both Docker images for quran-7clip-app and quran-n8n

echo "Building quran-7clip-app:latest..."
sudo nerdctl build -t quran-7clip-app:latest ./app

echo ""
echo "Building quran-n8n:latest..."
sudo nerdctl build -t quran-n8n:latest ./n8n

echo ""
echo "Build complete!"
echo "Images created:"
echo "  - quran-7clip-app:latest"
echo "  - quran-n8n:latest"
