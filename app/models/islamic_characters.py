"""
Islamic Character Models
ระบบจัดการ Character Models สำหรับเนื้อหาอิสลาม
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
import json
from pathlib import Path


class CharacterType(str, Enum):
    """ประเภทตัวละครอิสลาม"""
    SCHOLAR = "scholar"      # นักวิชาการ (Sheikh)
    YOUTH = "youth"          # เยาวชน
    SISTER = "sister"        # พี่สาวมุสลิม
    ELDER = "elder"          # ผู้สูงอายุ
    GENERIC = "generic"      # ทั่วไป


class AttireStyle(str, Enum):
    """แบบเครื่องแต่งกาย"""
    THOBE = "thobe"          # เสื้อคลุมอาหรับ
    TRADITIONAL = "traditional"  # แบบดั้งเดิม
    MODERN = "modern"        # แบบสมัยใหม่
    HIJAB = "hijab"          # ผ้าคลุม


class ContentSpecialization(str, Enum):
    """ความเชี่ยวชาญด้านเนื้อหา"""
    QURAN = "Quran"
    HADITH = "Hadith"
    TAFSIR = "Tafsir"
    AQIDAH = "Aqidah"
    FIQH = "Fiqh"
    DAWAH = "Dawah"
    LIFESTYLE = "Lifestyle"
    FAMILY = "Family"
    WOMEN = "Women in Islam"
    YOUTH = "Youth"
    WARNINGS = "Warnings"
    REMINDERS = "Reminders"


class VoicePreset(str, Enum):
    """Presets สำหรับเสียง"""
    SCHOLAR_DEEP = "scholar_deep"
    YOUTH_ENERGETIC = "youth_energetic"
    GENTLE_REMINDER = "gentle_reminder"
    SISTER_SOFT = "sister_soft"
    ELDER_WARM = "elder_warm"


class IslamicCharacter(BaseModel):
    """
    โมเดลตัวละครอิสลาม
    
    Attributes:
        name: ชื่อตัวละคร
        character_type: ประเภทตัวละคร
        description: คำอธิบาย
        image_path: เส้นทางรูปภาพ
        voice_id: ID เสียง (ElevenLabs)
        avatar_id: ID Avatar (HeyGen)
        languages: รายชื่อภาษาที่รองรับ
        specializations: ความเชี่ยวชาญด้านเนื้อหา
        attire: แบบเครื่องแต่งกาย
        beard: มีเคราหรือไม่ (สำหรับผู้ชาย)
        hijab: สวมผ้าคลุมหรือไม่ (สำหรับผู้หญิง)
        age_range: ช่วงอายุ
        voice_preset: Preset เสียง
    """
    name: str = Field(..., description="ชื่อตัวละคร")
    character_type: CharacterType = Field(..., description="ประเภทตัวละคร")
    description: str = Field(..., description="คำอธิบายตัวละคร")
    image_path: str = Field(..., description="เส้นทางรูปภาพ")
    
    # Voice & Avatar IDs
    voice_id: Optional[str] = Field(None, description="ID เสียง (ElevenLabs)")
    avatar_id: Optional[str] = Field(None, description="ID Avatar (HeyGen)")
    
    # Language & Content
    languages: List[str] = Field(
        default_factory=lambda: ["th-TH", "ar-SA", "en-US"],
        description="ภาษาที่รองรับ"
    )
    specializations: List[ContentSpecialization] = Field(
        default_factory=list,
        description="ความเชี่ยวชาญ"
    )
    
    # Appearance
    attire: AttireStyle = Field(AttireStyle.TRADITIONAL, description="แบบเครื่องแต่งกาย")
    beard: bool = Field(True, description="มีเคราหรือไม่")
    hijab: bool = Field(False, description="สวมผ้าคลุมหรือไม่")
    age_range: str = Field("30-50", description="ช่วงอายุ")
    
    # Voice Settings
    voice_preset: VoicePreset = Field(VoicePreset.SCHOLAR_DEEP, description="Preset เสียง")
    voice_settings: Dict[str, float] = Field(
        default_factory=lambda: {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.35
        },
        description="การตั้งค่าเสียง"
    )
    
    # Status
    is_active: bool = Field(True, description="เปิดใช้งานหรือไม่")
    is_premium: bool = Field(False, description="เป็น Premium หรือไม่")
    
    @field_validator('specializations', mode='before')
    @classmethod
    def parse_specializations(cls, v):
        if isinstance(v, list):
            return [ContentSpecialization(x) if isinstance(x, str) else x for x in v]
        return v
    
    class Config:
        use_enum_values = True


class CharacterManager:
    """
    ระบบจัดการ Character Models
    
    Features:
    - โหลดตัวละครเริ่มต้น
    - เลือกตัวละครที่เหมาะสมกับเนื้อหา
    - บันทึก/โหลดตัวละครจากไฟล์
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(exist_ok=True)  # Ensure directory exists
        self.characters: List[IslamicCharacter] = []
        self.load_default_characters()
    
    def load_default_characters(self):
        """โหลดตัวละครเริ่มต้น"""
        
        # ===== Sheikh - นักวิชาการ =====
        sheikh = IslamicCharacter(
            name="Sheikh Ahmad Al-Thai",
            character_type=CharacterType.SCHOLAR,
            description="นักวิชาการอิสลามผู้เมตตา เชี่ยวชาญ Quran และ Hadith ด้วยความรู้อันลึกซึ้ง",
            image_path="assets/characters/sheikh_ahmad.jpg",
            languages=["th-TH", "ar-SA", "en-US"],
            specializations=[
                ContentSpecialization.QURAN,
                ContentSpecialization.HADITH,
                ContentSpecialization.TAFSIR,
                ContentSpecialization.AQIDAH
            ],
            attire=AttireStyle.THOBE,
            beard=True,
            age_range="45-60",
            voice_preset=VoicePreset.SCHOLAR_DEEP,
            voice_settings={
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.35
            }
        )
        
        # ===== Youth - เยาวชน =====
        youth = IslamicCharacter(
            name="Omar Young Muslim",
            character_type=CharacterType.YOUTH,
            description="เยาวชนมุสลิมกระตือรือร้นในการเรียนรู้และแบ่งปันความรู้",
            image_path="assets/characters/omar_youth.jpg",
            languages=["th-TH", "en-US"],
            specializations=[
                ContentSpecialization.LIFESTYLE,
                ContentSpecialization.DAWAH,
                ContentSpecialization.YOUTH
            ],
            attire=AttireStyle.MODERN,
            beard=False,
            age_range="18-25",
            voice_preset=VoicePreset.YOUTH_ENERGETIC,
            voice_settings={
                "stability": 0.50,
                "similarity_boost": 0.75,
                "style": 0.65
            }
        )
        
        # ===== Sister - นักวิชาการหญิง =====
        sister = IslamicCharacter(
            name="Sister Aisha",
            character_type=CharacterType.SISTER,
            description="นักวิชาการหญิงผู้เชี่ยวชาญเรื่องสตรีในอิสลามและครอบครัว",
            image_path="assets/characters/sister_aisha.jpg",
            languages=["th-TH", "ar-SA", "en-US"],
            specializations=[
                ContentSpecialization.WOMEN,
                ContentSpecialization.FAMILY,
                ContentSpecialization.LIFESTYLE
            ],
            attire=AttireStyle.HIJAB,
            hijab=True,
            age_range="28-40",
            voice_preset=VoicePreset.SISTER_SOFT,
            voice_settings={
                "stability": 0.80,
                "similarity_boost": 0.70,
                "style": 0.25
            }
        )
        
        # ===== Elder - ผู้อาวุโส =====
        elder = IslamicCharacter(
            name="Grandpa Hassan",
            character_type=CharacterType.ELDER,
            description="ผู้อาวุโสผู้มีประสบการณ์ คอยให้คำแนะนำและกำลังใจ",
            image_path="assets/characters/grandpa_hassan.jpg",
            languages=["th-TH", "ar-SA"],
            specializations=[
                ContentSpecialization.REMINDERS,
                ContentSpecialization.WARNINGS,
                ContentSpecialization.FIQH
            ],
            attire=AttireStyle.THOBE,
            beard=True,
            age_range="60-75",
            voice_preset=VoicePreset.ELDER_WARM,
            voice_settings={
                "stability": 0.85,
                "similarity_boost": 0.80,
                "style": 0.20
            }
        )
        
        self.characters.extend([sheikh, youth, sister, elder])
    
    def get_character(self, name: str) -> Optional[IslamicCharacter]:
        """ดึงตัวละครตามชื่อ"""
        name_lower = name.lower()
        for char in self.characters:
            if char.name.lower() == name_lower or char.name.lower().replace(" ", "_") == name_lower:
                return char
        return None
    
    def get_character_by_type(self, character_type: CharacterType) -> List[IslamicCharacter]:
        """ดึงตัวละครตามประเภท"""
        return [c for c in self.characters if c.character_type == character_type and c.is_active]
    
    def select_character_for_content(
        self,
        content_type: str,
        topic: str,
        target_audience: str = "general"
    ) -> IslamicCharacter:
        """
        เลือกตัวละครที่เหมาะสมกับเนื้อหา
        
        Args:
            content_type: ประเภทเนื้อหา (reminder, warning, quran, hadith, etc.)
            topic: หัวข้อ
            target_audience: กลุ่มเป้าหมาย (general, youth, women, etc.)
            
        Returns:
            IslamicCharacter: ตัวละครที่เหมาะสม
        """
        
        # Topic-based selection
        topic_lower = topic.lower()
        content_lower = content_type.lower()
        
        # Warning/Akhirah content -> Scholar or Elder
        if any(kw in topic_lower for kw in ["hellfire", "นรก", "วันปรโลก", "กิยามะฮฺ", "warning", "警告"]):
            return self.get_character("Sheikh Ahmad Al-Thai") or self.characters[0]
        
        # Quran/Hadith/Tafsir -> Scholar
        if any(kw in topic_lower for kw in ["quran", "al-quran", "hadith", "tafsir", "อัลกุรอาน", "หะดีษ"]):
            return self.get_character("Sheikh Ahmad Al-Thai") or self.characters[0]
        
        # Youth content
        if target_audience == "youth" or any(kw in topic_lower for kw in ["youth", "เยาวชน", "วัยรุ่น", "young"]):
            return self.get_character("Omar Young Muslim") or self.characters[1]
        
        # Women/Family content
        if target_audience == "women" or any(kw in topic_lower for kw in ["women", "family", "ครอบครัว", "wife", "แม่"]):
            return self.get_character("Sister Aisha") or self.characters[2]
        
        # Reminders/Daily content -> Anyone
        if any(kw in content_lower for kw in ["reminder", "เตือน", "daily", "ประจำ"]):
            # Alternate between characters for variety
            return self.characters[0]  # Default to Sheikh
        
        # Default to Sheikh
        return self.characters[0]
    
    def add_character(self, character: IslamicCharacter) -> bool:
        """เพิ่มตัวละครใหม่"""
        # Check for duplicate
        if self.get_character(character.name):
            return False
        
        self.characters.append(character)
        return True
    
    def update_character(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> Optional[IslamicCharacter]:
        """อัปเดตตัวละคร"""
        character = self.get_character(name)
        if not character:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(character, key):
                setattr(character, key, value)
        
        return character
    
    def remove_character(self, name: str) -> bool:
        """ลบตัวละคร"""
        character = self.get_character(name)
        if character:
            self.characters.remove(character)
            return True
        return False
    
    def save_to_file(self, filepath: str) -> bool:
        """บันทึกตัวละครลงไฟล์"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            filepath = self.data_dir / filepath
            
            data = [char.model_dump() for char in self.characters]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Error saving characters: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """โหลดตัวละครจากไฟล์"""
        try:
            filepath = self.data_dir / filepath
            
            if not filepath.exists():
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.characters = [IslamicCharacter(**item) for item in data]
            return True
        except Exception as e:
            print(f"❌ Error loading characters: {e}")
            return False
    
    def list_characters(self) -> List[Dict[str, Any]]:
        """รายการตัวละครทั้งหมด"""
        return [
            {
                "name": char.name,
                "type": char.character_type.value,
                "description": char.description,
                "avatar_id": char.avatar_id,
                "voice_id": char.voice_id,
                "is_active": char.is_active,
                "specializations": [s.value for s in char.specializations]
            }
            for char in self.characters
        ]
    
    def get_active_characters(self) -> List[IslamicCharacter]:
        """ดึงตัวละครที่เปิดใช้งาน"""
        return [c for c in self.characters if c.is_active]


# ============= Factory Function =============

def create_character_manager(data_dir: Optional[str] = None) -> CharacterManager:
    """Factory function สำหรับสร้าง Character Manager"""
    return CharacterManager(data_dir)


# ============= Example Usage =============

def main():
    """ตัวอย่างการใช้งาน"""
    
    # สร้าง Character Manager
    manager = CharacterManager()
    
    # แสดงรายการตัวละคร
    print("📋 Characters:")
    for char in manager.list_characters():
        print(f"  - {char['name']} ({char['type']})")
    
    # เลือกตัวละครสำหรับเนื้อหา
    character = manager.select_character_for_content(
        content_type="reminder",
        topic="Hellfire warnings",
        target_audience="general"
    )
    
    print(f"\n🎭 Selected character: {character.name}")
    print(f"   Description: {character.description}")
    print(f"   Voice preset: {character.voice_preset.value}")
    print(f"   Specializations: {[s.value for s in character.specializations]}")


if __name__ == "__main__":
    main()
