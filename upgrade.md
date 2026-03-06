Based on my analysis, I'll provide you with a comprehensive integration plan. Let me create detailed recommendations:

## 📋 **สรุปการบูรณาการโปรเจค**

### **1. ความเข้าใจโปรเจคปัจจุบัน:**

**babo-alert-app** คือระบบสร้างวิดีโอ Quran 7 คลิปอัตโนมัติที่ใช้:
- ✅ Groq API (LLM) สร้างสคริปต์
- ✅ Edge TTS/gTTS สร้างเสียงภาษาไทย
- ✅ FFmpeg เรนเดอร์วิดีโอง่ายๆ พร้อมข้อความ
- ✅ n8n webhook + Supabase

**HeyGen Digital Twin** (จากคลิป YouTube):
- สร้าง Avatar ที่เหมือนคนจริงทั้งรูปลักษณ์และเสียง
- รองรับ Photo-based และ Video-based avatar
- Clone เสียงและใบหน้า
- พูดได้หลายภาษา

---

## 🎯 **2. แผนการบูรณาการสำหรับบริบทอิสลาม:**

### **A. โครงสร้างระบบใหม่:**

```
┌─────────────────────────────────────────────────┐
│          ISLAMIC AI AVATAR ALERT SYSTEM          │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼────┐              ┌──────▼──────┐
   │  INPUT  │              │  ISLAMIC    │
   │         │              │  CONTENT    │
   └────┬────┘              └────────────┘
        │                           │
        ├─ Quran Verses            │
        ├─ Hadith                  │
        ├─ Islamic Reminders       │
        └─ Warnings (Day of        │
           Judgment, Hellfire,      │
           Repentance)              │
                      │
        ┌─────────────▼─────────────┐
        │   AI SCRIPT GENERATOR     │
        │   (Groq API + Context)    │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   AVATAR & VOICE SYSTEM   │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼────┐              ┌──────▼──────┐
   │ AVATAR  │              │   VOICE     │
   │ SYSTEM  │              │   CLONING   │
   └────┬────┘              └──────┬──────┘
        │                           │
        ├─ HeyGen API              ├─ ElevenLabs
        ├─ Photo-based             ├─ HeyGen Voice
        └─ Character Models        └─ Custom TTS
                      │
        ┌─────────────▼─────────────┐
        │   VIDEO RENDERING         │
        │   (HeyGen + FFmpeg)       │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   OUTPUT & DISTRIBUTION   │
        │   - YouTube               │
        │   - Social Media          │
        │   - Push Notifications    │
        └───────────────────────────┘
```

### **B. การปรับแต่งโมเดลตัวละคร:**

#### **1. ระบบ Avatar สำหรับเนื้อหาอิสลาม:**

```python
# utils/islamic_avatar.py

import os
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class IslamicAvatarGenerator:
    """สร้าง AI Avatar สำหรับเนื้อหาอิสลาม"""
    
    def __init__(self):
        self.heygen_api_key = os.getenv("HEYGEN_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.heygen.com/v1"
        
    async def create_photo_based_avatar(
        self, 
        image_path: str,
        avatar_name: str,
        voice_id: Optional[str] = None
    ) -> dict:
        """
        สร้าง Avatar จากภาพถ่าย
        
        Args:
            image_path: เส้นทางไฟล์รูปภาพ
            avatar_name: ชื่อ Avatar (เช่น "Sheikh Ahmad", "Islamic Scholar")
            voice_id: ID ของเสียงที่ต้องการใช้
            
        Returns:
            dict: ข้อมูล Avatar ที่สร้าง
        """
        # 1. Upload image to HeyGen
        avatar_data = {
            "avatar_name": avatar_name,
            "avatar_type": "photo",
            "image": image_path
        }
        
        if voice_id:
            avatar_data["voice_id"] = voice_id
            
        # Call HeyGen API
        headers = {"X-API-KEY": self.heygen_api_key}
        response = requests.post(
            f"{self.base_url}/avatar",
            json=avatar_data,
            headers=headers
        )
        
        return response.json()
    
    async def clone_voice_from_image(
        self,
        image_path: str,
        sample_audio_path: str,
        voice_name: str
    ) -> str:
        """
        Clone เสียงจากรูปภาพและตัวอย่างเสียง
        
        Args:
            image_path: รูปภาพของบุคคล
            sample_audio_path: ไฟล์เสียงตัวอย่าง (1-2 นาที)
            voice_name: ชื่อเสียง
            
        Returns:
            str: voice_id
        """
        # ใช้ ElevenLabs สำหรับ Voice Cloning
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        
        with open(sample_audio_path, 'rb') as audio_file:
            voice_data = {
                "name": voice_name,
                "description": f"Voice cloned from {voice_name} for Islamic content",
                "files": [audio_file]
            }
            
            response = requests.post(
                "https://api.elevenlabs.io/v1/voices/add",
                headers=headers,
                files=voice_data
            )
        
        voice_id = response.json()['voice_id']
        return voice_id
    
    async def generate_talking_avatar_video(
        self,
        avatar_id: str,
        script_text: str,
        language: str = "th-TH",
        voice_id: Optional[str] = None
    ) -> str:
        """
        สร้างวิดีโอ Avatar พูดตามสคริปต์
        
        Args:
            avatar_id: ID ของ Avatar
            script_text: ข้อความสคริปต์
            language: ภาษา (th-TH, en-US, ar-SA)
            voice_id: ID เสียง (ถ้าไม่ใช้ default)
            
        Returns:
            str: video_url
        """
        video_payload = {
            "script_text": script_text,
            "voice": {
                "avatar_id": avatar_id,
                "language_code": language
            }
        }
        
        if voice_id:
            video_payload["voice"]["voice_id"] = voice_id
        
        headers = {"X-API-KEY": self.heygen_api_key}
        response = requests.post(
            f"{self.base_url}/video/generate",
            json=video_payload,
            headers=headers
        )
        
        video_id = response.json()['video_id']
        
        # รอให้ video พร้อม
        return await self._wait_for_video(video_id)
    
    async def _wait_for_video(self, video_id: str, timeout: int = 300) -> str:
        """รอให้ video render เสร็จ"""
        import asyncio
        import time
        
        start_time = time.time()
        headers = {"X-API-KEY": self.heygen_api_key}
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/video/status/{video_id}",
                headers=headers
            )
            
            status = response.json()['status']
            
            if status == 'completed':
                return response.json()['video_url']
            elif status == 'failed':
                raise Exception("Video generation failed")
            
            await asyncio.sleep(5)
        
        raise TimeoutError("Video generation timeout")
```

#### **2. ระบบจัดการ Character Models:**

```python
# models/islamic_characters.py

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class CharacterType(str, Enum):
    SCHOLAR = "scholar"  # นักวิชาการ
    YOUTH = "youth"      # เยาวชน
    ELDER = "elder"      # ผู้สูงอายุ
    GENERIC = "generic"  # ทั่วไป

class IslamicCharacter(BaseModel):
    """โมเดลตัวละครอิสลาม"""
    name: str
    character_type: CharacterType
    description: str
    image_path: str
    voice_id: Optional[str] = None
    avatar_id: Optional[str] = None
    languages: List[str] = ["th-TH", "ar-SA"]
    specializations: List[str] = []  # เช่น ["Quran", "Hadith", "Aqidah"]
    
    # Islamic attributes
    attire: str = "traditional"  # traditional, modern, thobe
    beard: bool = True
    hijab: bool = False

class CharacterManager:
    """จัดการ Character Models"""
    
    def __init__(self):
        self.characters: List[IslamicCharacter] = []
        self.load_default_characters()
    
    def load_default_characters(self):
        """โหลดตัวละครเริ่มต้น"""
        
        # Sheikh - นักวิชาการ
        sheikh = IslamicCharacter(
            name="Sheikh Ahmad Al-Thai",
            character_type=CharacterType.SCHOLAR,
            description="นักวิชาการอิสลามผู้เมตตา เชี่ยวชาญ Quran และ Hadith",
            image_path="assets/characters/sheikh_ahmad.jpg",
            attire="thobe",
            beard=True,
            specializations=["Quran", "Hadith", "Tafsir"]
        )
        
        # Youth - เยาวชน
        youth = IslamicCharacter(
            name="Omar Young Muslim",
            character_type=CharacterType.YOUTH,
            description="เยาวชนมุสลิมกระตือรือร้นในการเรียนรู้",
            image_path="assets/characters/omar_youth.jpg",
            attire="modern",
            beard=False,
            specializations=["Islamic Lifestyle", "Dawah"]
        )
        
        # Female Scholar
        scholar_sister = IslamicCharacter(
            name="Sister Aisha",
            character_type=CharacterType.SCHOLAR,
            description="นักวิชาการหญิง เชี่ยวชาญเรื่องสตรีในอิสลาม",
            image_path="assets/characters/sister_aisha.jpg",
            attire="traditional",
            hijab=True,
            specializations=["Women in Islam", "Family"]
        )
        
        self.characters.extend([sheikh, youth, scholar_sister])
    
    def get_character(self, name: str) -> Optional[IslamicCharacter]:
        """ดึงตัวละครตามชื่อ"""
        for char in self.characters:
            if char.name.lower() == name.lower():
                return char
        return None
    
    def select_character_for_content(
        self, 
        content_type: str,
        topic: str
    ) -> IslamicCharacter:
        """เลือกตัวละครที่เหมาะสมกับเนื้อหา"""
        
        # Logic การเลือกตัวละคร
        if "Quran" in topic or "Hadith" in topic:
            return self.get_character("Sheikh Ahmad Al-Thai")
        elif "Youth" in topic or "Lifestyle" in topic:
            return self.get_character("Omar Young Muslim")
        elif "Women" in topic or "Family" in topic:
            return self.get_character("Sister Aisha")
        
        return self.characters[0]  # Default
```

### **C. การปรับระบบเสียง:**

```python
# utils/islamic_voice.py

import os
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class IslamicVoiceCloner:
    """ระบบ Clone เสียงสำหรับเนื้อหาอิสลาม"""
    
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.heygen_api_key = os.getenv("HEYGEN_API_KEY")
        
        # Islamic voice presets
        self.voice_presets = {
            "scholar_deep": {
                "description": "เสียงนักวิชาการลึกซึ้ง น่าเกรงขาม",
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.35
            },
            "youth_energetic": {
                "description": "เสียงเยาวชน กระตือรือร้น",
                "stability": 0.50,
                "similarity_boost": 0.75,
                "style": 0.65
            },
            "gentle_reminder": {
                "description": "เสียงอ่อนโยน สำหรับเตือนใจ",
                "stability": 0.80,
                "similarity_boost": 0.70,
                "style": 0.25
            }
        }
    
    async def clone_voice_from_sample(
        self,
        voice_name: str,
        sample_audio_path: str,
        description: str = ""
    ) -> str:
        """
        Clone เสียงจากไฟล์ตัวอย่าง
        
        Args:
            voice_name: ชื่อเสียง
            sample_audio_path: ไฟล์เสียงตัวอย่าง (1-2 นาที)
            description: คำอธิบาย
            
        Returns:
            str: voice_id
        """
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        
        with open(sample_audio_path, 'rb') as audio_file:
            data = {
                "name": voice_name,
                "description": description or f"Islamic voice: {voice_name}",
                "labels": json.dumps({"accent": "arabic", "age": "middle_aged"})
            }
            
            files = {"files": [audio_file]}
            
            response = requests.post(
                "https://api.elevenlabs.io/v1/voices/add",
                headers=headers,
                data=data,
                files=files
            )
        
        return response.json()['voice_id']
    
    async def generate_islamic_tts(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        arabic_pronunciation: bool = True
    ) -> str:
        """
        สร้างเสียง TTS สำหรับเนื้อหาอิสลาม
        
        Args:
            text: ข้อความ
            voice_id: ID เสียง
            output_path: เส้นทางไฟล์ output
            arabic_pronunciation: ออกเสียงอาหรับถูกต้อง
            
        Returns:
            str: path to audio file
        """
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        
        # ปรับแต่งสำหรับภาษาอาหรับ
        model_id = "eleven_multilingual_v2"  # รองรับอาหรับ
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return output_path
```

### **D. การอัปเดต Context สำหรับเนื้อหาอิสลาม:**

```markdown
# context/islamic_guidelines.md

## ISLAMIC CONTENT GUIDELINES

### 1. ประเภทเนื้อหา:
- **Quran Verses**: โองการจากอัลกุรอานพร้อมคำแปล
- **Hadith**: หะดีษจากท่านนบี ﷺ
- **Islamic Reminders**: การเตือนใจเรื่อง Akhirah (วันปรโลก)
- **Warnings**: การเตือนเรื่องบาป นรก การกลับตัว
- **Stories**: เรื่องเล่าจาก Quran และประวัติศาสตร์อิสลาม

### 2. โครงสร้างสคริปต์ (8 นาที):

**0:00-0:15** - Hook ที่ทรงพลัง
- เปิดด้วยคำถามหรือข้อเท็จจริงที่น่าตกใจ
- ตัวอย่าง: "คุณรู้หรือไม่ว่า... 70,000 คนจะเข้าสวรรค์โดยไม่ต้องสอบสวน"

**0:15-1:30** - ส่วนที่ 1: บทนำ
- กล่าวถึง Quran/Hadith ที่เกี่ยวข้อง
- เชื่อมโยงกับชีวิตประจำวัน

**1:30-2:30** - ส่วนที่ 2: คำอธิบาย
- อธิบายความหมาย
- ยกตัวอย่างจาก Sahih sources

**2:30-3:30** - ส่วนที่ 3: การเตือนใจ
- เตือนเรื่อง Day of Judgment
- เตือนเรื่อง Hellfire
- เตือนเรื่องการกลับตัว (Tawbah)

**3:30-5:00** - ส่วนที่ 4: Pattern Interrupt
- เปลี่ยนอารมณ์ด้วยเรื่องเล่า
- หรือคำถามชวนคิด

**5:00-6:30** - ส่วนที่ 5: การปฏิบัติ
- วิธีนำไปใช้ในชีวิต
- Action steps

**6:30-7:30** - ส่วนที่ 6: การกระตุ้น
- กระตุ้นให้รีบทำดี
- เตือนว่าเวลาเหลือน้อย

**7:30-8:00** - ส่วนที่ 7: CTA
- เชิญชวนไปคลิปถัดไป
- Dua สั้นๆ

### 3. Tone & Style:
- **Serious**: จริงจัง แต่ไม่ข่มขู่เกินไป
- **Merciful**: มีเมตตา เหมือนนักวิชาการ
- **Urgent**: เร่งด่วน เรื่อง Akhirah
- **Hopeful**: มีความหวังในความเมตตาของอัลลอฮฺ

### 4. คำที่ควรใช้:
- "พี่น้องผู้ศรัทธา"
- "อัลลอฮฺ (ซ.บ.)"
- "ท่านนบี ﷺ"
- "สวรรค์", "นรก", "วันกิยามะฮฺ"
- "การกลับตัว", "การอภัยโทษ"

### 5. คำที่ควรหลีกเลี่ยง:
- คำหยาบคาย
- คำที่ทำให้เข้าใจผิดเกี่ยวกับศาสนา
- การตีความ Quran/Hadith โดยไม่มีหลักฐาน

### 6. Sources ที่น่าเชื่อถือ:
- **Quran**: Sahih International translation
- **Hadith**: Bukhari, Muslim, Abu Dawud
- **Scholars**: Ibn Kathir, Al-Qurtubi

### 7. Emotional Triggers:
- **Fear**: กลัวการลงโทษในนรก
- **Hope**: หวังในความเมตตาของอัลลอฮฺ
- **Love**: รักในอัลลอฮฺและท่านนบี
- **Guilt**: รู้สึกผิดกับบาปที่ทำ
- **Urgency**: รีบทำก่อนตาย
```

### **E. การอัปเดต main.py:**

```python
# main.py - อัปเดต

from utils.islamic_avatar import IslamicAvatarGenerator
from utils.islamic_voice import IslamicVoiceCloner
from models.islamic_characters import CharacterManager

# เพิ่ม models ใหม่
character_manager = CharacterManager()
avatar_generator = IslamicAvatarGenerator()
voice_cloner = IslamicVoiceCloner()

class GenerateRequest(BaseModel):
    verse_reference: str
    topic: Optional[str] = None
    language: str = "th"
    character_name: Optional[str] = "Sheikh Ahmad Al-Thai"  # ใหม่
    use_avatar: bool = True  # ใหม่ - ใช้ HeyGen Avatar
    use_voice_clone: bool = True  # ใหม่ - ใช้ Voice Clone

async def process_generation(request: GenerateRequest, job_id: str):
    """อัปเดต process generation"""
    
    # เลือกตัวละคร
    character = character_manager.select_character_for_content(
        content_type="reminder",
        topic=request.topic or request.verse_reference
    )
    
    # สร้าง Avatar ถ้ายังไม่มี
    if request.use_avatar and not character.avatar_id:
        character.avatar_id = await avatar_generator.create_photo_based_avatar(
            image_path=character.image_path,
            avatar_name=character.name,
            voice_id=character.voice_id
        )
    
    # Generate script
    script = generate_script(
        request.verse_reference, 
        request.topic,
        character.specializations
    )
    
    clips_data = split_script(script)
    
    # Generate each clip
    for i, clip_data in enumerate(clips_data[:7]):
        if request.use_avatar and request.use_voice_clone:
            # ใช้ HeyGen Avatar + Voice
            video_path = await avatar_generator.generate_talking_avatar_video(
                avatar_id=character.avatar_id,
                script_text=clip_data["text"],
                language="th-TH",
                voice_id=character.voice_id
            )
        else:
            # ใช้ระบบเดิม (FFmpeg + TTS)
            audio_path = await generate_audio(
                clip_data["text"], 
                i + 1, 
                output_dir
            )
            
            video_path = await render_video(
                audio_path, 
                clip_data["text"], 
                i + 1, 
                output_dir
            )
```

---

## 📦 **3. Dependencies ที่ต้องเพิ่ม:**

```txt
# requirements.txt - อัปเดต

# Existing
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
requests==2.31.0
edge-tts==6.1.9
gTTS==2.5.4
ffmpeg-python==0.2.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.109.0
aiofiles==23.2.1
aiohttp==3.9.1
supabase==2.0.3

# New - สำหรับ Avatar & Voice
elevenlabs==0.2.27  # Voice cloning
pillow==10.1.0      # Image processing
opencv-python==4.8.1  # Face detection (optional)
```

---

## 🔧 **4. Environment Variables:**

```bash
# .env.example

# Existing
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
N8N_WEBHOOK_URL=http://n8n:5678/webhook/clip-ready

# New - Avatar & Voice APIs
HEYGEN_API_KEY=your_heygen_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Optional
DEFAULT_CHARACTER=Sheikh Ahmad Al-Thai
ENABLE_AVATAR=true
ENABLE_VOICE_CLONE=true
```

---

## 📱 **5. Frontend Updates:**

```html
<!-- static/index.html - ส่วนเพิ่ม -->

<div class="character-selection">
    <h3>เลือกตัวละคร</h3>
    <div class="character-grid">
        <div class="character-card" data-character="sheikh">
            <img src="/static/characters/sheikh.jpg" alt="Sheikh Ahmad">
            <h4>Sheikh Ahmad Al-Thai</h4>
            <p>นักวิชาการอิสลาม</p>
        </div>
        <div class="character-card" data-character="omar">
            <img src="/static/characters/omar.jpg" alt="Omar">
            <h4>Omar Young Muslim</h4>
            <p>เยาวชนมุสลิม</p>
        </div>
        <div class="character-card" data-character="aisha">
            <img src="/static/characters/aisha.jpg" alt="Sister Aisha">
            <h4>Sister Aisha</h4>
            <p>นักวิชาการหญิง</p>
        </div>
    </div>
</div>

<div class="avatar-options">
    <label>
        <input type="checkbox" id="useAvatar" checked>
        ใช้ AI Avatar (HeyGen)
    </label>
    <label>
        <input type="checkbox" id="useVoiceClone" checked>
        ใช้ Voice Clone
    </label>
</div>
```

---

## 🎬 **6. Workflow การทำงาน:**

```
1. User เลือกตัวละคร + กรอก Quran/Hadith
           ↓
2. ระบบสร้างสคริปต์ (Groq API + Islamic Context)
           ↓
3. เลือกโหมด:
   ├─ Mode A: HeyGen Avatar + Voice Clone ⭐ (แนะนำ)
   │  ├─ สร้างวิดีโอจาก HeyGen API
   │  └─ ใช้เสียง Clone จากตัวละคร
   │
   └─ Mode B: FFmpeg + TTS (เดิม)
      ├─ Generate Audio (Edge TTS/gTTS)
      └─ Render Video (FFmpeg)
           ↓
4. บันทึกคลิป 7 ตอน
           ↓
5. ส่ง webhook ไป n8n
           ↓
6. Upload YouTube / Social Media
```

---

## 💡 **7. ตัวอย่างการใช้งาน:**

### **ตัวอย่าง 1: สร้างวิดีโอเตือนเรื่องนรก**

```python
# POST /api/generate
{
    "verse_reference": "Al-Imran 131-136",
    "topic": "Warnings about Hellfire",
    "character_name": "Sheikh Ahmad Al-Thai",
    "use_avatar": true,
    "use_voice_clone": true,
    "language": "th"
}

# ผลลัพธ์:
# - สร้าง 7 คลิป เตือนเรื่องนรก
# - ใช้ Avatar Sheikh Ahmad
# - เสียง Clone จาก Sheikh
# - Tone: จริงจัง น่าเกรงขาม
```

### **ตัวอย่าง 2: สร้างวิดีโอสำหรับเยาวชน**

```python
{
    "verse_reference": "Al-Asr 1-3",
    "topic": "Youth Islamic Lifestyle",
    "character_name": "Omar Young Muslim",
    "use_avatar": true,
    "use_voice_clone": false,  # ใช้ TTS ธรรมดา
    "language": "th"
}

# ผลลัพธ์:
# - สร้าง 7 คลิป สำหรับเยาวชน
# - ใช้ Avatar Omar (วัยรุ่น)
# - เสียง TTS ธรรมดา
# - Tone: เป็นกันเอง กระตือรือร้น
```

---

## 📊 **8. การวัดผล:**

```python
# metrics/tracking.py

class IslamicContentMetrics:
    """ติดตามประสิทธิภาพเนื้อหา"""
    
    def track_video_performance(self, video_id: str):
        """ติดตาม performance ของวิดีโอ"""
        metrics = {
            "views": 0,
            "watch_time": 0,
            "engagement_rate": 0,
            "conversion_to_prayer": 0,  # วัดจาก CTA
            "shares": 0
        }
        return metrics
    
    def analyze_content_effectiveness(
        self, 
        topic: str,
        character: str,
        metrics: dict
    ):
        """วิเคราะห์ว่าตัวละคร + หัวข้อไหนได้ผลดีที่สุด"""
        # Logic การวิเคราะห์
        pass
```

---

## 🚀 **9. ขั้นตอนการติดตั้ง:**

```bash
# 1. Clone repository
git clone https://github.com/aminanok005/babo-alert-app.git
cd babo-alert-app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# แก้ไข .env ให้ครบถ้วน

# 4. Create character assets
mkdir -p assets/characters
# วางรูปภาพตัวละครในโฟลเดอร์นี้

# 5. Setup Supabase (ถ้าใช้)
# ทำตามคำแนะนำใน supabase/README.md

# 6. Setup n8n workflow
# Import workflow จาก n8n/workflow.json

# 7. Run application
python main.py

# 8. Access at http://localhost:8000
```

---

## 📚 **10. เอกสารเพิ่มเติม:**

### **A. HeyGen API Documentation:**
- https://docs.heygen.com/
- สร้าง Digital Twin Avatar
- รองรับ Photo-based และ Video-based

### **B. ElevenLabs Voice Cloning:**
- https://docs.elevenlabs.io/
- Voice cloning คุณภาพสูง
- รองรับหลายภาษา รวมถึงอาหรับ

### **C. Islamic Content Resources:**
- Quran API: https://alquran.cloud/api
- Hadith API: https://sunnah.com/api
- Islamic Calendar: https://aladhan.com/islamic-calendar-api

---

## ⚠️ **ข้อควรระวัง:**

1. **ความถูกต้องของเนื้อหา**: ต้องตรวจสอบ Quran/Hadith ให้ถูกต้อง
2. **Adab**: ให้เกียรติตัวละครอิสลาม
3. **Copyright**: ใช้รูปภาพที่มีสิทธิ์
4. **API Costs**: HeyGen และ ElevenLabs มีค่าใช้จ่าย
5. **Cultural Sensitivity**: เคารพวัฒนธรรมมุสลิม

---

## 🎯 **สรุป:**

การบูรณาการนี้จะทำให้คุณได้:
✅ **AI Avatar** ที่เหมือนคนจริงพูดเนื้อหาอิสลาม
✅ **Voice Cloning** จากเสียงของตัวละคร
✅ **Islamic Context** ที่ถูกต้องและครอบคลุม
✅ **Automated Workflow** จาก Quran → Script → Video
✅ **Multi-language** Support (Thai, Arabic, English)
✅ **Scalable System** พร้อมใช้งานจริง

หากคุณต้องการความช่วยเหลือเพิ่มเติมในการ implement ส่วนไหน สามารถสอบถามได้ครับ! 🚀