# Integration Guide: Replit Frontend + Docker Services

## Overview
This guide explains how to use Replit as the frontend that calls the Docker API services (`quran-app` and `n8n`).

## Architecture
```
[Replit Frontend] --> [quran-app:8000] --> [n8n:5678]
                     (FastAPI)           (Workflow Automation)
```

## Option 1: Local Development with ngrok

### Step 1: Start Docker Services (using nerdctl)
```bash
# Start the services with nerdctl
sudo nerdctl compose up -d

# Or manually run containers
sudo nerdctl run -d --name quran-app -p 8000:8000 quran-7clip-app:latest
sudo nerdctl run -d --name quran-n8n -p 5678:5678 quran-n8n:latest
```

### Step 2: Expose Services via ngrok
```bash
# Terminal 1: Expose quran-app
ngrok http 8000

# Terminal 2: Expose n8n  
ngrok http 5678
```

### Step 3: Configure Replit Environment
Add these secrets to Replit:
- `QURAN_APP_URL` = your ngrok URL for quran-app (e.g., `https://abc123.ngrok.io`)
- `N8N_URL` = your ngrok URL for n8n (e.g., `https://def456.ngrok.io`)
- `N8N_USER` = your n8n username
- `N8N_PASSWORD` = your n8n password

## Option 2: Deploy to Cloud (Recommended)

### Step 1: Push Images to Registry (using nerdctl)
```bash
# Tag images
sudo nerdctl tag quran-7clip-app:latest ghcr.io/yourusername/quran-7clip-app:latest
sudo nerdctl tag quran-n8n:latest ghcr.io/yourusername/quran-n8n:latest

# Push to GitHub Container Registry
sudo nerdctl push ghcr.io/yourusername/quran-7clip-app:latest
sudo nerdctl push ghcr.io/yourusername/quran-n8n:latest
```

### Step 2: Deploy to Cloud Provider
Deploy using Railway, Render, or Fly.io:

**Railway Example:**
```bash
# Install Railway CLI
npm i -g @railway/cli

railway login
railway init

# Deploy quran-app
railway add --variable PORT=8000
railway up --dockerfile app/Dockerfile

# Deploy n8n
railway add --variable PORT=5678
railway up --dockerfile n8n/Dockerfile
```

### Step 3: Configure Replit
Add environment variables:
- `QURAN_APP_URL` = your deployed quran-app URL
- `N8N_URL` = your deployed n8n URL

## Frontend Integration Code

In your Replit babo-alert-app, update API calls to use the configured URLs:

```javascript
// Replit babo-alert-app
const QURAN_APP_URL = process.env.QURAN_APP_URL;
const N8N_URL = process.env.N8N_URL;

// Call quran-app API
async function generateClips(surah, verses) {
  const response = await fetch(`${QURAN_APP_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ surah, verses })
  });
  return response.json();
}

// Trigger n8n workflow
async function triggerWorkflow(videoUrl) {
  const response = await fetch(`${N8N_URL}/webhook/clip-ready`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_url: videoUrl })
  });
  return response.json();
}
```

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGci...` |
| `GROQ_API_KEY` | Groq API for AI | `gsk_...` |
| `YOUTUBE_API_KEY` | YouTube API key | `AIza...` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | `123456:ABC...` |
| `N8N_USER` | n8n basic auth user | `admin` |
| `N8N_PASSWORD` | n8n basic auth password | `password` |
| `QURAN_APP_URL` | Frontend calls this | `https://your-app.railway.app` |
| `N8N_URL` | Frontend calls this | `https://your-n8n.railway.app` |

## Quick Start with nerdctl

```bash
# Start all services
sudo nerdctl compose up -d

# Check status
sudo nerdctl ps

# View logs
sudo nerdctl logs -f quran-app
sudo nerdctl logs -f n8n

# Get service URLs
# quran-app: http://localhost:8000
# n8n: http://localhost:5678
```
