# 📺 Quran 7-Clip Generator

ระบบสร้างคลิปวิดีโอ 7 ตอนจากอายา�ะฮฺ อัตโนมัติ ด้วย AI

## 📋 สารบัญ

- [ภาพรวมระบบ](#-ภาพรวมระบบ)
- [ข้อกำหนดเบื้องต้น](#-ข้อกำหนดเบื้องต้น)
- [การติดตั้ง](#-การติดตั้ง)
- [การตั้งค่า Environment Variables](#-การตั้งค่า-environment-variables)
- [การรันระบบ](#-การรันระบบ)
- [การใช้งาน](#-การใช้งาน)
- [Debugging](#-debugging)
- [Deployment](#-deployment)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ ภาพรวมระบบ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│   n8n Workflow  │────▶│  Social Media   │
│   (Port 8000)   │     │   (Port 5678)   │     │  Upload         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│   Supabase DB   │                           │   YouTube       │
│                 │                           │   Telegram      │
└─────────────────┘                           └─────────────────┘
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `quran-7clip-app` | 8000 | FastAPI แอปหลัก สำหรับสร้างคลิป |
| `quran-n8n` | 5678 | n8n Workflow Automation |

---

## ✅ ข้อกำหนดเบื้องต้น

- **Docker** & **Docker Compose**
- **nerdctl** (สำหรับ build images บน Linux) หรือใช้ **docker build**
- **Supabase Project** (ฐานข้อมูล)
- **API Keys** ต่างๆ (ดูใน .env.example)

---

## 🚀 การติดตั้ง

### 1. Clone โปรเจกต์

```bash
cd /home/nisreen/ai-lab/n8n/babo-alert-app
```

### 2. สร้าง Environment File

```bash
cp .env.example .env
```

### 3. แก้ไข .env

เปิดไฟล์ `.env` และใส่ค่า API Keys:

```bash
nano .env
```

---

## ⚙️ การตั้งค่า Environment Variables

```bash
# ===== LLM & AI =====
GROQ_API_KEY=your_groq_api_key_here

# ===== Supabase =====
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key_here

# ===== YouTube =====
YOUTUBE_API_KEY=your_youtube_api_key_here

# ===== Telegram =====
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# ===== n8n =====
N8N_USER=admin
N8N_PASSWORD=your_n8n_password_here
N8N_API_KEY=your_n8n_api_key_here
N8N_WEBHOOK_URL=http://n8n:5678/webhook/clip-ready
```

### การขอ API Keys

| Service | วิธีขอ |
|---------|--------|
| **GROQ** | https://console.groq.com/keys |
| **Supabase** | https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api |
| **YouTube** | https://console.cloud.google.com/apis/credentials |
| **Telegram** | @BotFather ใน Telegram |

---

## 🎯 การรันระบบ

### วิธีที่ 1: ใช้ Docker Compose (แนะนำ)

```bash
# Build และ Run ทุก services
docker-compose up -d --build
```

### วิธีที่ 2: Build Images ก่อน

```bash
# Build images ด้วย script
bash scripts/build_images.sh

# หรือ build ด้วย docker
docker build -t quran-7clip-app:latest ./app
docker build -t quran-n8n:latest ./n8n
```

### วิธีที่ 3: Run เฉพาะ Service

```bash
# Run แค่ FastAPI app
docker-compose up quran-app -d

# Run แค่ n8n
docker-compose up n8n -d
```

---

## 🔧 การตรวจสอบสถานะ

```bash
# ดู containers ที่กำลังทำงาน
docker-compose ps

# ดู logs
docker-compose logs -f quran-app
docker-compose logs -f n8n

# ดู logs ทุก service
docker-compose logs -f
```

---

## 📱 การใช้งาน

### เปิด Web Interface

```
http://localhost:8000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | สร้างคลิปใหม่ |
| GET | `/api/status/{job_id}` | ดูสถานะงาน |
| GET | `/api/download/{job_id}/{clip_number}` | ดาวน์โหลดคลิป |
| GET | `/api/context/{type}` | ดึง context |

### ตัวอย่างการเรียก API

```bash
# สร้างคลิปใหม่
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "verse_reference": "Al-Anbiya 1-3",
    "topic": "การรับรู้ของความจริง",
    "language": "th"
  }'

# ดูสถานะ (แทนที่ JOB_ID)
curl http://localhost:8000/api/status/JOB_ID
```

### n8n Workflow

เปิด n8n UI ที่: **http://localhost:5678**

```
User: admin
Password: (ตามที่ตั้งใน N8N_PASSWORD)
```

---

## 🐛 Debugging

### ดู Logs แบบ Real-time

```bash
# App logs
docker-compose logs -f quran-app

# n8n logs
docker-compose logs -f n8n

# ดู logs ทุก container
docker-compose logs -f --tail=100
```

### เข้าไปใน Container

```bash
# เข้า app container
docker exec -it quran-7clip-app bash

# เข้า n8n container
docker exec -it quran-n8n bash
```

### ตรวจสอบ Environment Variables

```bash
# ดู environment ใน container
docker exec quran-7clip-app env
```

### ตรวจสอบ Port ที่ใช้

```bash
# ดู port ที่ใช้
netstat -tlnp | grep -E '8000|5678'

# หรือ
ss -tlnp | grep -E '8000|5678'
```

### Debug Common Issues

#### 1. Container ไม่ start

```bash
# ดู error logs
docker-compose logs quran-app

# ลอง rebuild
docker-compose build --no-cache quran-app
docker-compose up -d
```

#### 2. ไม่สามารถเชื่อมต่อ n8n

```bash
# ตรวจสอบ network
docker network inspect babo-alert-app_quran-network

# ตรวจสอบ DNS
docker exec quran-7clip-app ping -c 3 n8n
```

#### 3. TTS Error (Edge TTS 403)

ระบบมี fallback เป็น gTTS อัตโนมัติ หาก Edge TTS เกิด error

#### 4. Supabase Connection Error

```bash
# ตรวจสอบ .env
docker exec quran-7clip-app env | grep SUPABASE
```

---

## 🚢 Deployment

### สำหรับ Production

1. **แก้ไข docker-compose.yml** สำหรับ production:

```yaml
services:
  quran-app:
    # ... existing config
    environment:
      - DEBUG=false
      # ใช้ production database
      - DATABASE_URL=${SUPABASE_URL}
```

2. **ใช้ HTTPS** (แนะนำ nginx reverse proxy)

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

3. **Setup Supabase Production**

```bash
# รัน SQL ใน Supabase SQL Editor
# ดูไฟล์: supabase/schema.sql
```

### Deploy บน Server

```bash
# 1. Clone project
git clone https://github.com/your-repo/babo-alert-app.git
cd babo-alert-app

# 2. สร้าง .env
cp .env.example .env
nano .env

# 3. Build และ Run
docker-compose up -d --build

# 4. ตรวจสอบ
docker-compose ps
docker-compose logs -f
```

### Docker Swarm (Optional)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml babo-alert
```

---

## 📡 API Reference

### POST `/api/generate`

สร้างคลิปวิดีโอใหม่

**Request Body:**
```json
{
  "verse_reference": "Al-Anbiya 1-3",
  "topic": "การรับรู้ของความจริง",
  "language": "th"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "total_clips": 7,
  "status": "processing",
  "clips": [
    {"clip_number": 1, "status": "pending", "video_url": null}
  ]
}
```

### GET `/api/status/{job_id}`

ดูสถานะการทำงาน

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "total_clips": 7,
  "completed": 3,
  "clips": [
    {"clip_number": 1, "status": "completed", "video_url": "/output/..."}
  ]
}
```

---

## ⚠️ Troubleshooting

### ปัญหาที่พบบ่อย

| ปัญหา | วิธีแก้ |
|-------|--------|
| `Connection refused` | ตรวจสอบว่า container ทำงานอยู่ `docker-compose ps` |
| `SUPABASE_KEY error` | ตรวจสอบ .env และ API key |
| `n8n webhook failed` | ตรวจสอบ N8N_WEBHOOK_URL และ N8N_API_KEY |
| `TTS not working` | ตรวจสอบ internet connection |
| `FFmpeg error` | ตรวจสอบว่าติดตั้งใน Dockerfile แล้ว |

### กู้คืนระบบ

```bash
# Stop ทุกอย่าง
docker-compose down

# Remove volumes (⚠️ ลบข้อมูลทั้งหมด)
docker-compose down -v

# Rebuild และ run ใหม่
docker-compose up -d --build
```

---

## 📁 โครงสร้างโปรเจกต์

```
babo-alert-app/
├── app/                    # FastAPI application
│   ├── Dockerfile
│   ├── main.py            # Main application
│   ├── requirements.txt
│   ├── utils/             # Utility modules
│   │   ├── script_generator.py
│   │   ├── tts_generator.py
│   │   ├── video_renderer.py
│   │   └── youtube_update.py
│   ├── static/            # Frontend files
│   │   ├── index.html
│   │   ├── script.js
│   │   └── style.css
│   ├── context/           # AI context files
│   └── assets/            # Static assets
├── n8n/                   # n8n workflows
│   ├── Dockerfile
│   └── workflows/
├── scripts/               # Build & test scripts
├── supabase/             # Database schema
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔐 Security Notes

- **เปลี่ยน N8N_PASSWORD** ก่อน deploy production
- **ใช้ HTTPS** สำหรับ production
- **จำกัดสิทธิ์ Supabase** ใช้ anon key สำหรับ public operations
- **เก็บ .env** ไว้ในที่ปลอดภัย ไม่ commit ขึ้น git

---

## 📄 License

MIT License

---

## 🆘 การขอความช่วยเหลือ

หากมีปัญหา ให้ดู:

1. Logs: `docker-compose logs -f`
2. ตรวจสอบ .env ว่ากรอกครบถ้วน
3. ตรวจสอบว่า API keys ถูกต้อง
4. ตรวจสอบ network connectivity
