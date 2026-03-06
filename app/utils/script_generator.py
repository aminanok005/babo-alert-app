import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# โหลดไฟล์ Context
CONTEXT_DIR = Path("context")

def load_context_file(filename):
    """โหลดเนื้อหาจากไฟล์ .md ในโฟลเดอร์ context"""
    file_path = CONTEXT_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_full_context():
    """รวม context ทั้งหมดสำหรับส่งให้ AI"""
    memory = load_context_file("memory.md")
    knowledge = load_context_file("knowledge.md")
    skills = load_context_file("skills.md")
    
    return f"""
# CONTEXT FOR AI GENERATION

## Memory (Project Guidelines)
{memory}

## Knowledge (Quranic Content)
{knowledge}

## Skills (Production Standards)
{skills}
"""

def generate_script(verse_reference, topic=None):
    """สร้างสคริปต์จาก AI โดยใช้ Context"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    context = get_full_context()
    
    prompt = f"""{context}

---
# TASK
เขียนสคริปต์วิดีโอศาสนาอิสลามจาก {verse_reference}
แบ่งเป็น 7 ส่วนชัดเจนตามโครงสร้างใน memory.md

## Requirements:
1. ความยาวรวมประมาณ 1,150 คำ (สำหรับ 8 นาที)
2. ภาษาไทยเข้าใจง่าย ไม่ใช้คำอาหรับยากโดยไม่จำเป็น
3. มี Hook ภายใน 15 วินาทีแรก
4. มี Pattern Interrupt ทุก 1 นาที
5. มี CTA เชื่อมไปตอนต่อไป
6. Tone: จริงจัง, ปลุกใจ, มีเมตตา

## Output Format:
เขียนเป็น 7 ส่วนชัดเจน โดยแต่ละส่วนขึ้นต้นด้วยตัวเลข 1-7
"""
    
    if topic:
        prompt += f"\nหัวข้อเพิ่มเติม: {topic}"
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "คุณคือผู้เขียนสคริปต์วิดีโอศาสนาอิสลามมืออาชีพ"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    resp = requests.post(url, json=payload, headers=headers)
    
    if resp.status_code != 200:
        raise Exception(f"Groq API Error: {resp.text}")
    
    return resp.json()['choices'][0]['message']['content']

def split_script(full_script):
    """แยกสคริปต์เป็น 7 ส่วน"""
    lines = [l.strip() for l in full_script.split('\n') if l.strip()]
    clips = []
    current = ""
    
    for line in lines:
        # ตรวจสอบว่าขึ้นต้นด้วยตัวเลข 1-7
        if line[0].isdigit() and len(clips) < 7:
            if current: 
                clips.append({"text": current.strip()})
            current = line
        else:
            current += " " + line
    
    if current: 
        clips.append({"text": current.strip()})
    
    # ถ้าได้น้อยกว่า 7 ส่วน ให้แบ่งเท่าๆ กัน
    if len(clips) < 7:
        words = " ".join([c["text"] for c in clips]).split()
        words_per_clip = len(words) // 7
        clips = []
        for i in range(7):
            start = i * words_per_clip
            end = start + words_per_clip if i < 6 else len(words)
            clips.append({"text": " ".join(words[start:end])})
    
    return clips[:7]