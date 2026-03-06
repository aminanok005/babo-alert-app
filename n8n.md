# 🚀 Production-Ready: Quran 7-Clip Generator
## Docker + Supabase + nerdctl + n8n Social Media Automation

> 🎯 **เป้าหมาย**: ระบบผลิตวิดีโออัตโนมัติที่พร้อมใช้งานจริง เก็บข้อมูลใน Supabase และอัพโหลดโซเชียลผ่าน n8n  
> 💰 **ต้นทุน**: $0-30/เดือน (Lean Stack)

---

## 📂 1. โครงสร้างโปรเจกต์ที่อัปเดต

```
quran-7clip-prod/
├── app/                          # แอปหลัก (FastAPI)
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── context/
│   ├── utils/
│   └── static/
├── n8n/                          # n8n Workflow
│   ├── workflows/
│   │   └── social-upload.json
│   └── Dockerfile
├── docker-compose.yml            # รวมทุกบริการ
├── .env                          # Environment Variables
├── supabase/
│   └── schema.sql                # Database Schema
└── scripts/
    ├── deploy.sh                 # สคริปต์ deploy ด้วย nerdctl
    └── backup.sh                 # สคริปต์ backup
```

---

## 🐳 2. Dockerfile สำหรับแอปหลัก (`app/Dockerfile`)

```dockerfile
# app/Dockerfile
FROM python:3.11-slim

# ติดตั้ง dependencies ของระบบ
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-ibm-plex \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ตั้งค่า working directory
WORKDIR /app

# คัดลอก requirements และติดตั้ง
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดแอป
COPY . .

# สร้างโฟลเดอร์ที่จำเป็น
RUN mkdir -p output context utils static assets/fonts

# ตั้งค่า environment
ENV PYTHONUNBUFFERED=1
ENV FONT_PATH=/usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf

# เปิดพอร์ต
EXPOSE 8000

# คำสั่งรัน
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🐳 3. Dockerfile สำหรับ n8n (`n8n/Dockerfile`)

```dockerfile
# n8n/Dockerfile
FROM n8nio/n8n:latest

# ติดตั้ง dependencies เพิ่มเติมถ้าต้องการ
USER root
RUN npm install --save @n8n/n8n-nodes-supabase
USER node

# ตั้งค่า environment
ENV N8N_HOST=0.0.0.0
ENV N8N_PORT=5678
ENV N8N_PROTOCOL=http
ENV NODE_ENV=production

EXPOSE 5678
```

---

## 📋 4. docker-compose.yml (รวมทุกบริการ)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ===== แอปหลัก (FastAPI) =====
  quran-app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: quran-7clip-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - FONT_PATH=/usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook/clip-ready
    volumes:
      - ./app/output:/app/output
      - ./app/context:/app/context
      - ./app/assets:/app/assets
    depends_on:
      - n8n
    networks:
      - quran-network
    restart: unless-stopped

  # ===== n8n Workflow Automation =====
  n8n:
    build:
      context: ./n8n
      dockerfile: Dockerfile
    container_name: quran-n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=0.0.0.0
      - WEBHOOK_URL=http://localhost:5678/
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - FACEBOOK_PAGE_TOKEN=${FACEBOOK_PAGE_TOKEN}
      - TIKTOK_ACCESS_TOKEN=${TIKTOK_ACCESS_TOKEN}
    volumes:
      - ./n8n/workflows:/home/node/.n8n/workflows
      - n8n-data:/home/node/.n8n
    networks:
      - quran-network
    restart: unless-stopped

  # ===== PostgreSQL (Local Backup) =====
  postgres:
    image: postgres:15-alpine
    container_name: quran-postgres
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=quran_clips
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/backup.sh:/docker-entrypoint-initdb.d/backup.sh
    ports:
      - "5432:5432"
    networks:
      - quran-network
    restart: unless-stopped
    profiles:
      - local-db  # ใช้เมื่อต้องการ DB ในเครื่อง แทน Supabase

networks:
  quran-network:
    driver: bridge

volumes:
  n8n-data:
  postgres-data:
```

---

## 🗄️ 5. Supabase Schema (`supabase/schema.sql`)

```sql
-- supabase/schema.sql
-- รันใน Supabase SQL Editor

-- ===== ตารางโปรเจกต์ =====
CREATE TABLE projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    verse_reference TEXT NOT NULL,
    topic TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    user_id UUID REFERENCES auth.users(id)
);

-- ===== ตารางคลิป =====
CREATE TABLE clips (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    clip_number INTEGER NOT NULL,
    title TEXT,
    script_text TEXT,
    audio_path TEXT,
    video_path TEXT,
    video_url TEXT,
    thumbnail_url TEXT,
    status TEXT DEFAULT 'pending',
    duration_seconds INTEGER,
    youtube_url TEXT,
    telegram_message_id TEXT,
    facebook_post_id TEXT,
    tiktok_video_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ,
    UNIQUE(project_id, clip_number)
);

-- ===== ตารางการอัพโหลดโซเชียล =====
CREATE TABLE social_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- youtube, telegram, facebook, tiktok
    platform_id TEXT,
    platform_url TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== ตารางผู้ใช้ (ถ้าต้องการระบบสมาชิก) =====
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    subscription_plan TEXT DEFAULT 'free',
    clips_generated INTEGER DEFAULT 0,
    clips_limit INTEGER DEFAULT 50,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== Indexes สำหรับความเร็ว =====
CREATE INDEX idx_clips_project ON clips(project_id);
CREATE INDEX idx_clips_status ON clips(status);
CREATE INDEX idx_social_uploads_clip ON social_uploads(clip_id);
CREATE INDEX idx_projects_user ON projects(user_id);

-- ===== Row Level Security (RLS) =====
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_uploads ENABLE ROW LEVEL SECURITY;

-- Policy: ผู้ใช้เห็นข้อมูลของตัวเองเท่านั้น
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

## 🐍 6. อัปเดต `app/main.py` (เชื่อมต่อ Supabase)

```python
# เพิ่มใน main.py

from supabase import create_client, Client
import os

# Initialize Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ===== ในฟังก์ชัน process_generation() =====
async def process_generation(job_id: str, request: GenerateRequest):
    output_dir = Path(f"output/{job_id}")
    output_dir.mkdir(exist_ok=True)
    
    # สร้างโปรเจกต์ใน Supabase
    project_data = {
        "verse_reference": request.verse_reference,
        "topic": request.topic,
        "status": "processing"
    }
    
    try:
        project = supabase.table("projects").insert(project_data).execute()
        project_id = project.data[0]["id"]
        print(f"✅ Project created in Supabase: {project_id}")
    except Exception as e:
        print(f"⚠️ Supabase error: {e}")
        project_id = None
    
    try:
        # ... (โค้ดสร้างสคริปต์เดิม)
        
        for i, clip_data in enumerate(clips_data[:7]):
            # ... (สร้างคลิป)
            
            # บันทึกคลิปใน Supabase
            if project_id:
                clip_record = {
                    "project_id": project_id,
                    "clip_number": i + 1,
                    "script_text": clip_data["text"][:500],  # ตัดให้สั้น
                    "video_path": str(video_path),
                    "status": "completed"
                }
                supabase.table("clips").insert(clip_record).execute()
            
            # 🔥 ส่ง Webhook ไป n8n เมื่อคลิปพร้อม 🔥
            await notify_n8n_webhook({
                "job_id": job_id,
                "project_id": project_id,
                "clip_number": i + 1,
                "video_path": str(video_path),
                "video_url": f"/output/{job_id}/clip_{i + 1}.mp4"
            })
        
        # อัปเดตสถานะโปรเจกต์
        if project_id:
            supabase.table("projects").update({
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }).eq("id", project_id).execute()
            
    except Exception as e:
        # ... (จัดการข้อผิดพลาดเดิม)
        if project_id:
            supabase.table("projects").update({
                "status": "failed"
            }).eq("id", project_id).execute()

# ===== ฟังก์ชันส่ง Webhook ไป n8n =====
async def notify_n8n_webhook(data: dict):
    """ส่งข้อมูลคลิปที่พร้อมให้ n8n ประมวลผลต่อ"""
    import aiohttp
    
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/clip-ready")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                if response.status == 200:
                    print(f"✅ Webhook sent to n8n for clip {data['clip_number']}")
                else:
                    print(f"⚠️ n8n webhook failed: {response.status}")
    except Exception as e:
        print(f"⚠️ Failed to send n8n webhook: {e}")
```

---

## 📋 7. อัปเดต `app/requirements.txt`

```txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
requests==2.31.0
edge-tts==6.1.9
ffmpeg-python==0.2.0
aiofiles==23.2.1
supabase==2.0.3
aiohttp==3.9.1
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-api-python-client==2.109.0
```

---

## 🔄 8. n8n Workflow: Social Media Upload (`n8n/workflows/social-upload.json`)

```json
{
  "name": "Quran Clip - Social Upload",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "clip-ready",
        "responseMode": "lastNode"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.SUPABASE_URL }}/rest/v1/clips",
        "headers": {
          "apikey": "={{ $env.SUPABASE_KEY }}",
          "Authorization": "Bearer {{ $env.SUPABASE_KEY }}",
          "Content-Type": "application/json"
        },
        "body": {
          "status": "uploading"
        },
        "options": {}
      },
      "name": "Update Supabase Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [450, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.platform }}",
              "value2": "youtube"
            }
          ]
        }
      },
      "name": "Filter YouTube",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "https://www.googleapis.com/upload/youtube/v3/videos",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{ $env.YOUTUBE_API_KEY }}",
          "Content-Type": "application/json"
        },
        "body": {
          "snippet": {
            "title": "={{ $json.title }}",
            "description": "={{ $json.description }}"
          },
          "status": {
            "privacyStatus": "public"
          }
        }
      },
      "name": "Upload to YouTube",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [850, 200]
    },
    {
      "parameters": {
        "url": "https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendVideo",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "chat_id": "={{ $env.TELEGRAM_CHAT_ID }}",
          "video": "={{ $json.video_url }}"
        }
      },
      "name": "Upload to Telegram",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [850, 400]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.SUPABASE_URL }}/rest/v1/social_uploads",
        "headers": {
          "apikey": "={{ $env.SUPABASE_KEY }}",
          "Authorization": "Bearer {{ $env.SUPABASE_KEY }}"
        },
        "body": {
          "clip_id": "={{ $json.clip_id }}",
          "platform": "={{ $json.platform }}",
          "platform_url": "={{ $json.result_url }}",
          "status": "completed",
          "uploaded_at": "={{ $now }}"
        }
      },
      "name": "Save Upload Record",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Update Supabase Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Update Supabase Status": {
      "main": [
        [
          {
            "node": "Filter YouTube",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Filter YouTube": {
      "main": [
        [
          {
            "node": "Upload to YouTube",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Upload to Telegram",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  ]
}
```

---

## 📝 9. ไฟล์ `.env` (Environment Variables)

```bash
# .env

# ===== Supabase =====
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx

# ===== AI & TTS =====
GROQ_API_KEY=gsk_xxxxx
ELEVENLABS_API_KEY=xi_xxxxx

# ===== n8n =====
N8N_USER=admin
N8N_PASSWORD=your_secure_password
N8N_WEBHOOK_URL=http://n8n:5678/webhook/clip-ready

# ===== Social Media APIs =====
YOUTUBE_API_KEY=xxxxx
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=@your_channel
FACEBOOK_PAGE_TOKEN=xxxxx
TIKTOK_ACCESS_TOKEN=xxxxx

# ===== Database (Local) =====
DB_USER=quran_admin
DB_PASSWORD=secure_password_here

# ===== Docker =====
DOCKER_HOST=unix:///var/run/docker.sock
```

---

## 🚀 10. สคริปต์ Deploy ด้วย nerdctl (`scripts/deploy.sh`)

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Deploying Quran 7-Clip Generator with nerdctl..."

# 1. ตรวจสอบ nerdctl
if ! command -v nerdctl &> /dev/null; then
    echo "❌ nerdctl not found! Install from: https://github.com/containerd/nerdctl"
    exit 1
fi

# 2. โหลด environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 3. สร้าง Supabase schema (ถ้ายังไม่มี)
echo "📊 Setting up Supabase schema..."
# ต้องรัน manual ใน Supabase SQL Editor

# 4. Build images
echo "🐳 Building Docker images..."
nerdctl build -t quran-7clip-app:latest ./app
nerdctl build -t quran-n8n:latest ./n8n

# 5. Start services
echo "🚀 Starting services..."
nerdctl compose -f docker-compose.yml up -d

# 6. Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# 7. Check status
echo "📊 Service Status:"
nerdctl compose ps

# 8. Show access URLs
echo ""
echo "✅ Deployment Complete!"
echo "📱 App: http://localhost:8000"
echo "🔄 n8n: http://localhost:5678"
echo "🗄️ Postgres: localhost:5432"
echo ""
echo "📝 View logs: nerdctl compose logs -f"
echo "🛑 Stop: nerdctl compose down"
```

---

## 🎯 11. คำสั่งใช้งาน (Quick Commands)

```bash
# ===== Deploy =====
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# ===== ดูสถานะ =====
nerdctl compose ps

# ===== ดูล็อก =====
nerdctl compose logs -f quran-app
nerdctl compose logs -f n8n

# ===== รีสตาร์ท =====
nerdctl compose restart

# ===== หยุด =====
nerdctl compose down

# ===== ลบทั้งหมด (ระวัง!) =====
nerdctl compose down -v

# ===== Backup ข้อมูล =====
./scripts/backup.sh

# ===== อัปเดตโค้ด =====
git pull
nerdctl compose build
nerdctl compose up -d
```

---

## 📊 12. สถาปัตยกรรมระบบ (Architecture Diagram)

```
┌─────────────────────────────────────────────────────────────┐
│                      USER (Mobile/Web)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP Request
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI App (Port 8000)                     │
│  - Generate Script (Groq)                                    │
│  - Generate Audio (Edge-TTS)                                 │
│  - Render Video (FFmpeg)                                     │
│  - Save to Supabase                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ Webhook
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  n8n Workflow (Port 5678)                    │
│  - Receive Clip Ready Webhook                                │
│  - Upload to YouTube                                         │
│  - Upload to Telegram                                        │
│  - Upload to Facebook                                        │
│  - Upload to TikTok                                          │
│  - Update Supabase Status                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ API Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Supabase Cloud                              │
│  - projects table                                            │
│  - clips table                                               │
│  - social_uploads table                                      │
│  - users table                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 13. Checklist ก่อน Production

```
[ ] 1. สร้าง Supabase Project และรัน schema.sql
[ ] 2. ตั้งค่า .env ให้ครบทุกตัวแปร
[ ] 3. ติดตั้ง nerdctl และตรวจสอบการทำงาน
[ ] 4. สร้าง API Keys สำหรับโซเชียลมีเดียทั้งหมด
[ ] 5. ทดสอบสร้าง 1 คลิปในเครื่องก่อน
[ ] 6. ทดสอบ Webhook ไป n8n
[ ] 7. ทดสอบอัพโหลด YouTube (Private ก่อน)
[ ] 8. ตั้งค่า HTTPS (ใช้ Caddy/Nginx Reverse Proxy)
[ ] 9. ตั้งค่า Backup อัตโนมัติ
[ ] 10. ตั้งค่า Monitoring (Prometheus/Grafana หรือ Uptime Kuma)
```

---

## 🎁 Bonus: สคริปต์ Backup (`scripts/backup.sh`)

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "📦 Starting backup..."

# Backup Supabase data (ใช้ pg_dump ถ้าใช้ Local Postgres)
nerdctl exec quran-postgres pg_dump -U $DB_USER quran_clips > $BACKUP_DIR/db_backup.sql

# Backup output files
cp -r ./app/output $BACKUP_DIR/

# Backup n8n workflows
cp -r ./n8n/workflows $BACKUP_DIR/

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"

# Upload to Supabase Storage (optional)
# curl -X POST ...
```

---

> 🎯 **พร้อม Deploy แล้วครับ!**  
> ระบบนี้จะผลิต 7 คลิป → บันทึก Supabase → n8n อัพโหลดโซเชียลอัตโนมัติ  
> 
> หากต้องการให้ผมช่วย:
> - 🔹 สร้าง GitHub Actions สำหรับ CI/CD
> - 🔹 ตั้งค่า HTTPS ด้วย Caddy
> - 🔹 เพิ่มระบบ Authentication (Login/Signup)
> - 🔹 สร้าง Dashboard สำหรับดูสถิติ
> 
> บอกได้เลยครับ! 🛠️🤲