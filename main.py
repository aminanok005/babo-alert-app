import os
import asyncio
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid

# Import utility modules
from utils.script_generator import generate_script, split_script
from utils.tts_generator import generate_audio
from utils.video_renderer import render_video
from utils.youtube_upload import upload_to_youtube

app = FastAPI(title="Quran 7-Clip Generator")

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

# --- In-memory job storage (ใช้ SQLite ใน production) ---
jobs = {}


# เพิ่ม Route ใหม่ใน main.py

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
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "total_clips": 7,
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
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_clips": job["total_clips"],
        "completed": sum(1 for c in job["clips"] if c["status"] == "completed"),
        "clips": job["clips"]
    }

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
    
    try:
        # Step 1: Generate Script
        jobs[job_id]["clips"][0]["status"] = "processing"
        script = generate_script(request.verse_reference, request.topic)
        clips_data = split_script(script)
        
        # Step 2-7: Generate each clip
        for i, clip_data in enumerate(clips_data[:7]):
            clip_idx = i
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
            
            # Update status
            jobs[job_id]["clips"][clip_idx]["status"] = "completed"
            jobs[job_id]["clips"][clip_idx]["video_url"] = f"/output/{job_id}/clip_{clip_idx + 1}.mp4"
        
        jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

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