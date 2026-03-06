# 📦 README-DEV.md

> คำสั่งที่รันสำเร็จแล้วบนเครื่องนี้ สำหรับใช้กับ Replit

---

## ✅ Commands ที่รันสำเร็จแล้ว

### 1. สร้าง Environment File

```bash
cp .env.example .env
```

### 2. Build Docker Images (ใช้ nerdctl)

```bash
# Build app image
sudo nerdctl build -t quran-7clip-app:latest ./app

# Build n8n image
sudo nerdctl build -t quran-n8n:latest ./n8n
```

### 3. รัน Docker Compose

```bash
# Run all services
docker-compose up -d --build

# Run specific service
docker-compose up quran-app -d
docker-compose up n8n -d

# Stop services
docker-compose down
```

### 4. ตรวจสอบสถานะ

```bash
# ดู containers
docker-compose ps

# ดู logs
docker-compose logs -f quran-app
docker-compose logs -f n8n
```

### 5. เข้า Container

```bash
docker exec -it quran-7clip-app bash
docker exec -it quran-n8n bash
```

### 6. Test Workflow

```bash
# Test full 7-clip generation
python3 scripts/test_workflow.py "ความเมตตาของอัลลอฮ์"
```

---

## 🚀 สำหรับ Replit

### Pull Images จาก GitHub Container Registry

```bash
# Login to ghcr.io
sudo nerdctl login ghcr.io -u YOUR_GITHUB_USERNAME

# Pull images
sudo nerdctl pull ghcr.io/aminanok005/babo-alert-app:latest
sudo nerdctl pull ghcr.io/aminanok005/babo-alert-app-n8n:latest
```

### หรือ Build ใหม่บน Replit

```bash
# Build app
sudo nerdctl build -t quran-7clip-app:latest ./app

# Push to ghcr.io (ถ้าต้องการ)
sudo nerdctl push ghcr.io/aminanok005/babo-alert-app:latest
```

---

## 📋 Environment Variables ที่จำเป็น

```bash
# LLM
GROQ_API_KEY=your_groq_api_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key_here

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key_here

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# n8n
N8N_USER=admin
N8N_PASSWORD=your_n8n_password_here
N8N_API_KEY=your_n8n_api_key_here
N8N_WEBHOOK_URL=http://n8n:5678/webhook/clip-ready
```

---

## 🔧 Replit-Specific Commands

### ติดตั้ง Dependencies

```bash
# Install Python dependencies
pip install -r app/requirements.txt

# Install ffmpeg (if not available)
sudo apt-get update && sudo apt-get install -y ffmpeg
```

### รัน FastAPI Locally (Without Docker)

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### รัน n8n Locally

```bash
# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your_password \
  -e WEBHOOK_URL=http://localhost:5678/ \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

### ทดสอบ API

```bash
# Health check
curl http://localhost:8000/

# Generate clip
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "verse_reference": "Al-Anbiya 1-3",
    "topic": "ความเมตตาของอัลลอฮ์",
    "language": "th"
  }'

# Check status
curl http://localhost:8000/api/status/YOUR_JOB_ID
```

---

## 📁 Project Structure

```
babo-alert-app/
├── app/                    # FastAPI application
│   ├── Dockerfile          # Docker image definition
│   ├── main.py             # Main application
│   ├── requirements.txt    # Python dependencies
│   ├── utils/              # Utility modules
│   │   ├── script_generator.py
│   │   ├── tts_generator.py
│   │   ├── video_renderer.py
│   │   └── youtube_update.py
│   ├── static/             # Frontend files
│   └── context/            # AI context files
├── n8n/                    # n8n workflows
│   ├── Dockerfile
│   └── workflows/
├── scripts/                # Build & test scripts
│   ├── build_images.sh
│   ├── test_workflow.py
│   └── render_clip.sh
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🐛 Troubleshooting

### Container ไม่ Start

```bash
# ดู error logs
docker-compose logs quran-app

# Rebuild
docker-compose build --no-cache quran-app
docker-compose up -d
```

### Network Issues

```bash
# ตรวจสอบ network
docker network inspect babo-alert-app_quran-network

# ตรวจสอบ DNS
docker exec quran-7clip-app ping -c 3 n8n
```

### TTS Error

ระบบมี fallback เป็น gTTS อัตโนมัติ หาก Edge TTS เกิด error

---

## 📝 Notes

- ใช้ `nerdctl` แทน `docker` บน Linux environment
- สำหรับ Replit ให้ใช้ Docker container ที่ pre-built แล้ว
- n8n webhook URL: `http://n8n:5678/webhook/clip-ready`
- ต้องตั้งค่า N8N_API_KEY สำหรับ API access
