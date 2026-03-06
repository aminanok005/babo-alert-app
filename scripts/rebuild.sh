#!/bin/bash
# Rebuild script for babo-alert-app
# Rebuilds containers with latest code using sudo nerdctl

set -e

echo "🔨 Starting rebuild process..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ] && ! sudo -v 2>/dev/null; then
    echo "⚠️  This script requires sudo privileges for nerdctl"
    echo "Please run with: sudo $0"
    exit 1
fi

# Use sudo for nerdctl commands
NERDCTL="sudo nerdctl"

echo "📦 Building container images..."
$NERDCTL compose -f docker-compose.yml build --no-cache

echo "🛑 Stopping existing containers..."
$NERDCTL compose -f docker-compose.yml down

echo "🚀 Starting containers with new images..."
$NERDCTL compose -f docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

echo ""
echo "📊 Service Status:"
$NERDCTL compose -f docker-compose.yml ps

echo ""
echo "✅ Rebuild Complete!"
echo "📱 App: http://localhost:8000"
echo "🔄 n8n: http://localhost:5678"
echo ""
echo "📝 View logs:"
echo "   All:     sudo nerdctl compose -f docker-compose.yml logs -f"
echo "   App:     sudo nerdctl logs -f quran-7clip-app"
echo "   n8n:     sudo nerdctl logs -f quran-n8n"
echo ""
echo "🛑 To stop: sudo nerdctl compose -f docker-compose.yml down"
