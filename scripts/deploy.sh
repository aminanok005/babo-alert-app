#!/bin/bash
# Deployment script for babo-alert-app
# Uses nerdctl compose to manage services

set -e

echo "🚀 Starting services..."
nerdctl compose -f docker-compose.yml down && nerdctl compose -f docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "📊 Service Status:"
nerdctl compose ps

echo ""
echo "✅ Deployment Complete!"
echo "📱 App: http://localhost:8000"
echo "🔄 n8n: http://localhost:5678"
echo "🗄️ Postgres: localhost:5432"
echo ""
echo "📝 View logs: nerdctl compose logs -f"
echo "🛑 Stop: nerdctl compose down"
