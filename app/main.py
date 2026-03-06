import os
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import utility modules
from utils.script_generator import generate_script, split_script
from utils.tts_generator import generate_audio
from utils.video_renderer import render_video
from utils.youtube_update import upload_to_youtube

# Context directory
CONTEXT_DIR = Path("context")

app = FastAPI(title="Quran 7-Clip Generator")

# Initialize Supabase (optional)
supabase_client = None
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected")
    except Exception as e:
        print(f"⚠️ Supabase connection failed: {e}")
        supabase_client = None

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

# Create directories
Path("output").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("assets").mkdir(exist_ok=True)

# --- Request/Response Models ---
class GenerateRequest(BaseModel):
    verse_reference: str  # เช่น "Al-Anbiya 1-3"
    topic: Optional[str] = None
    language: str = "th"

class ClipStatus(BaseModel):
    clip_number: int
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class GenerateResponse(BaseModel):
    job_id: str
    total_clips: int
    status: str
    clips: List[ClipStatus]

# --- In-memory job storage ---
jobs = {}


# ===== Helper Functions =====

async def notify_n8n_webhook(data: dict):
    """ส่งข้อมูลคลิปที่พร้อมให้ n8n ประมวลผลต่อ"""
    import aiohttp
    
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/clip-ready")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                if response.status == 200:
                    print(f"✅ Webhook sent to n8n for clip {data.get('clip_number')}")
                else:
                    print(f"⚠️ n8n webhook failed: {response.status}")
    except Exception as e:
        print(f"⚠️ Failed to send n8n webhook: {e}")


def save_to_supabase(table: str, data: dict):
    """บันทึกข้อมูลลง Supabase"""
    if not supabase_client:
        return None
    
    try:
        result = supabase_client.table(table).insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"⚠️ Supabase insert error: {e}")
        return None


def update_supabase(table: str, data: dict, filter_field: str, filter_value):
    """อัปเดตข้อมูลใน Supabase"""
    if not supabase_client:
        return None
    
    try:
        result = supabase_client.table(table).update(data).eq(filter_field, filter_value).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"⚠️ Supabase update error: {e}")
        return None


# ===== API Routes =====

@app.get("/api/context/{context_type}")
async def get_context(context_type: str):
    """ดึงข้อมูล Context สำหรับแสดงใน Frontend"""
    context_file = CONTEXT_DIR / f"{context_type}.md"
    
    if not context_file.exists():
        raise HTTPException(status_code=404, detail="Context file not found")
    
    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"type": context_type, "content": content}


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_clips(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    # สร้างโปรเจกต์ใน Supabase (ถ้ามี)
    project_id = None
    if supabase_client:
        project_data = {
            "verse_reference": request.verse_reference,
            "topic": request.topic,
            "status": "processing",
            "name": f"Project {job_id[:8]}"
        }
        result = save_to_supabase("projects", project_data)
        if result:
            project_id = result.get("id")
            print(f"✅ Project created in Supabase: {project_id}")
    
    # เก็บ project_id ไว้ใน job
    jobs[job_id] = {
        "status": "processing",
        "total_clips": 7,
        "project_id": project_id,
        "clips": [
            {"clip_number": i+1, "status": "pending", "video_url": None}
            for i in range(7)
        ]
    }
    
    # Run in background
    background_tasks.add_task(process_generation, job_id, request)
    
    return GenerateResponse(
        job_id=job_id,
        total_clips=7,
        status="processing",
        clips=[ClipStatus(**clip) for clip in jobs[job_id]["clips"]]
    )


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "total_clips": job["total_clips"],
        "completed": sum(1 for c in job["clips"] if c["status"] == "completed"),
        "clips": job["clips"]
    }
    
    if "error" in job:
        response["error"] = job["error"]
    
    return response


@app.get("/api/download/{job_id}/{clip_number}")
async def download_clip(job_id: str, clip_number: int):
    file_path = f"output/{job_id}/clip_{clip_number}.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type="video/mp4")


# --- Background Processing ---
async def process_generation(job_id: str, request: GenerateRequest):
    output_dir = Path(f"output/{job_id}")
    output_dir.mkdir(exist_ok=True)
    
    job = jobs.get(job_id)
    project_id = job.get("project_id") if job else None
    
    try:
        # Step 1: Generate Script
        if job:
            jobs[job_id]["clips"][0]["status"] = "processing"
        
        script = generate_script(request.verse_reference, request.topic)
        clips_data = split_script(script)
        
        # Step 2-7: Generate each clip
        for i, clip_data in enumerate(clips_data[:7]):
            clip_idx = i
            
            if job:
                jobs[job_id]["clips"][clip_idx]["status"] = "processing"
            
            # Generate Audio
            audio_path = await generate_audio(
                clip_data["text"], 
                clip_idx + 1, 
                output_dir
            )
            
            # Generate Video
            video_path = await render_video(
                audio_path, 
                clip_data["text"], 
                clip_idx + 1, 
                output_dir
            )
            
            video_url = f"/output/{job_id}/clip_{clip_idx + 1}.mp4"
            
            if job:
                # Update status
                jobs[job_id]["clips"][clip_idx]["status"] = "completed"
                jobs[job_id]["clips"][clip_idx]["video_url"] = video_url
            
            # บันทึกคลิปใน Supabase
            if project_id and supabase_client:
                clip_record = {
                    "project_id": project_id,
                    "clip_number": clip_idx + 1,
                    "script_text": clip_data["text"][:500],
                    "video_path": str(video_path),
                    "video_url": video_url,
                    "status": "completed"
                }
                save_to_supabase("clips", clip_record)
            
            # 🔥 ส่ง Webhook ไป n8n เมื่อคลิปพร้อม 🔥
            await notify_n8n_webhook({
                "job_id": job_id,
                "project_id": project_id,
                "clip_number": clip_idx + 1,
                "video_path": str(video_path),
                "video_url": video_url,
                "status": "completed"
            })
        
        # อัปเดตสถานะโปรเจกต์
        if project_id and supabase_client:
            update_supabase("projects", {
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }, "id", project_id)
        
        if job:
            jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        if job:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        
        # อัปเดตสถานะ failed ใน Supabase
        if project_id and supabase_client:
            update_supabase("projects", {"status": "failed"}, "id", project_id)
        
        print(f"Error processing job {job_id}: {str(e)}")


@app.post("/api/upload/{job_id}/{clip_number}")
async def upload_clip(job_id: str, clip_number: int):
    """Upload to YouTube"""
    file_path = f"output/{job_id}/clip_{clip_number}.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    video_url = await upload_to_youtube(file_path, f"Quran Clip {clip_number}")
    return {"success": True, "youtube_url": video_url}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
