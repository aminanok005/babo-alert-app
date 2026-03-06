## 🎯 **ระบบจัดการ Video List + Template Context ที่ชาญฉลาด**

ผมออกแบบระบบจัดการวิดีโอและเทมเพลตที่ครบวงจรสำหรับโปรเจคอิสลามของคุณ ดังนี้:

---

## 📊 **1. โครงสร้างข้อมูล (Database Schema)**

### **Supabase Tables Design:**

```sql
-- 1.1 ตารางเก็บวิดีโอที่สร้างแล้ว
CREATE TABLE generated_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    
    -- Islamic Content Metadata
    verse_reference TEXT,  -- เช่น "Al-Baqarah:255"
    hadith_reference TEXT, -- เช่น "Bukhari:1"
    topic_category TEXT,   -- เช่น "warnings", "reminders", "stories"
    content_type TEXT,     -- "quran", "hadith", "reminder", "story"
    
    -- Character & Avatar Info
    character_name TEXT,
    character_id TEXT,
    avatar_type TEXT,      -- "heygen", "ffmpeg"
    voice_id TEXT,
    
    -- Video Files
    video_url TEXT,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    file_size_mb NUMERIC,
    
    -- Generation Settings (JSON)
    generation_config JSONB,
    context_template_id UUID REFERENCES context_templates(id),
    
    -- Status & Tracking
    status TEXT DEFAULT 'processing', -- processing, completed, failed
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Engagement Metrics
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    
    -- Organization
    tags TEXT[],  -- เช่น ["hellfire", "repentance", "youth"]
    is_favorite BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_publish_at TIMESTAMPTZ
);

-- Indexes for smart search
CREATE INDEX idx_videos_search ON generated_videos USING gin(
    to_tsvector('thai', title || ' ' || COALESCE(description, ''))
);
CREATE INDEX idx_videos_category ON generated_videos(topic_category, content_type);
CREATE INDEX idx_videos_tags ON generated_videos USING gin(tags);
CREATE INDEX idx_videos_created ON generated_videos(created_at DESC);

-- 1.2 ตารางเก็บ Template/Context
CREATE TABLE context_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Islamic Context Settings
    content_type TEXT NOT NULL,  -- "quran", "hadith", "reminder"
    topic_category TEXT,
    
    -- Character Settings
    default_character TEXT,
    character_preferences JSONB,  -- {attire, beard, hijab, etc.}
    
    -- Script Structure
    script_structure JSONB,  -- {hook_duration, sections, cta_style}
    
    -- Tone & Style
    tone_settings JSONB,  -- {seriousness, mercy_level, urgency}
    
    -- Language & Voice
    language_code TEXT DEFAULT 'th-TH',
    voice_preferences JSONB,  -- {voice_id, stability, style}
    
    -- Islamic Guidelines
    islamic_guidelines JSONB,  -- {sources, scholars, avoid_topics}
    
    -- Output Settings
    output_settings JSONB,  -- {resolution, format, watermark}
    
    -- Organization
    tags TEXT[],
    is_public BOOLEAN DEFAULT false,  -- Share with team
    is_system_template BOOLEAN DEFAULT false,  -- Default templates
    
    -- Usage Tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT  -- User ID
);

-- 1.3 ตารางเก็บ Version History ของ Template
CREATE TABLE template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES context_templates(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Snapshot of settings
    settings_snapshot JSONB NOT NULL,
    
    change_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT
);

-- 1.4 ตารางเก็บ Video Playlists/Collections
CREATE TABLE video_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Islamic Series Info
    series_type TEXT,  -- "quran_tafsir", "hadith_series", "ramadan_series"
    target_audience TEXT,  -- "youth", "scholars", "general"
    
    -- Organization
    cover_image_url TEXT,
    is_published BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT
);

-- Junction table for videos in collections
CREATE TABLE collection_videos (
    collection_id UUID REFERENCES video_collections(id) ON DELETE CASCADE,
    video_id UUID REFERENCES generated_videos(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (collection_id, video_id)
);
```

---

## 🔧 **2. Backend API Endpoints**

### **Video Management API (`routes/videos.py`):**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import create_client
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json

router = APIRouter(prefix="/api/videos", tags=["videos"])

# Pydantic Models
class VideoFilter(BaseModel):
    status: Optional[str] = None
    content_type: Optional[str] = None
    topic_category: Optional[str] = None
    character_name: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_query: Optional[str] = None

class VideoListResponse(BaseModel):
    videos: List[dict]
    total: int
    page: int
    per_page: int
    has_more: bool

@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    filters: VideoFilter = Depends(),
    supabase=Depends(get_supabase_client)
):
    """List videos with smart filtering and search"""
    
    query = supabase.table("generated_videos").select(
        "*, context_templates(name, description)",
        count="exact"
    )
    
    # Apply filters
    if filters.status:
        query = query.eq("status", filters.status)
    if filters.content_type:
        query = query.eq("content_type", filters.content_type)
    if filters.topic_category:
        query = query.eq("topic_category", filters.topic_category)
    if filters.character_name:
        query = query.eq("character_name", filters.character_name)
    if filters.tags:
        query = query.contains("tags", filters.tags)
    if filters.date_from:
        query = query.gte("created_at", filters.date_from.isoformat())
    if filters.date_to:
        query = query.lte("created_at", filters.date_to.isoformat())
    
    # Full-text search
    if filters.search_query:
        query = query.text_search(
            "to_tsvector('thai', title || ' ' || coalesce(description, ''))",
            filters.search_query,
            type="websearch"
        )
    
    # Pagination
    from_ = (page - 1) * per_page
    result = query.order("created_at", desc=True).range(from_, from_ + per_page - 1).execute()
    
    return VideoListResponse(
        videos=result.data,
        total=result.count,
        page=page,
        per_page=per_page,
        has_more=from_ + per_page < result.count
    )

@router.get("/{video_id}")
async def get_video_detail(video_id: str, supabase=Depends(get_supabase_client)):
    """Get detailed video info with generation config"""
    result = supabase.table("generated_videos").select(
        "*, context_templates(*)"
    ).eq("id", video_id).single().execute()
    
    if not result.data:
        raise HTTPException(404, "Video not found")
    
    return result.data

@router.patch("/{video_id}")
async def update_video(
    video_id: str,
    updates: dict,
    supabase=Depends(get_supabase_client)
):
    """Update video metadata, tags, favorite status, etc."""
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.table("generated_videos").update(updates).eq("id", video_id).execute()
    return result.data[0]

@router.delete("/{video_id}")
async def delete_video(video_id: str, supabase=Depends(get_supabase_client)):
    """Soft delete video (archive)"""
    result = supabase.table("generated_videos").update(
        {"is_archived": True, "updated_at": datetime.utcnow().isoformat()}
    ).eq("id", video_id).execute()
    return {"success": True}

@router.post("/{video_id}/regenerate")
async def regenerate_video(
    video_id: str,
    regenerate_config: Optional[dict] = None,
    supabase=Depends(get_supabase_client)
):
    """Regenerate video with same or updated config"""
    # Get original video config
    original = supabase.table("generated_videos").select("*").eq("id", video_id).single().execute()
    
    if not original.data:
        raise HTTPException(404, "Video not found")
    
    # Merge configs if provided
    config = original.data["generation_config"]
    if regenerate_config:
        config.update(regenerate_config)
    
    # Queue new generation job
    job_id = await queue_generation_job(
        verse_reference=original.data["verse_reference"],
        generation_config=config,
        template_id=original.data["context_template_id"]
    )
    
    return {"job_id": job_id, "message": "Regeneration queued"}
```

### **Template Management API (`routes/templates.py`):**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/templates", tags=["templates"])

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    content_type: str
    topic_category: Optional[str] = None
    default_character: Optional[str] = None
    character_preferences: Optional[dict] = None
    script_structure: Optional[dict] = None
    tone_settings: Optional[dict] = None
    language_code: str = "th-TH"
    voice_preferences: Optional[dict] = None
    islamic_guidelines: Optional[dict] = None
    output_settings: Optional[dict] = None
    tags: Optional[List[str]] = None
    is_public: bool = False

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # ... other optional fields

@router.get("/", response_model=List[dict])
async def list_templates(
    search: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    include_system: bool = Query(True),
    supabase=Depends(get_supabase_client)
):
    """List context templates with filtering"""
    query = supabase.table("context_templates").select("*")
    
    if not include_system:
        query = query.eq("is_system_template", False)
    
    if content_type:
        query = query.eq("content_type", content_type)
    
    if tags:
        query = query.contains("tags", tags)
    
    if search:
        query = query.or_(
            f"name.ilike.%{search}%,description.ilike.%{search}%"
        )
    
    result = query.order("usage_count", desc=True).execute()
    return result.data

@router.post("/", status_code=201)
async def create_template(
    template: TemplateCreate,
    supabase=Depends(get_supabase_client),
    user=Depends(get_current_user)
):
    """Create new context template"""
    template_data = template.dict(exclude_unset=True)
    template_data["created_by"] = user.id
    
    # Create template
    result = supabase.table("context_templates").insert(template_data).execute()
    template_id = result.data[0]["id"]
    
    # Create initial version
    supabase.table("template_versions").insert({
        "template_id": template_id,
        "version_number": 1,
        "settings_snapshot": template_data,
        "change_log": "Initial creation",
        "created_by": user.id
    }).execute()
    
    return result.data[0]

@router.get("/{template_id}")
async def get_template(template_id: str, supabase=Depends(get_supabase_client)):
    """Get template with version history"""
    # Get template
    template = supabase.table("context_templates").select("*").eq("id", template_id).single().execute()
    
    if not template.data:
        raise HTTPException(404, "Template not found")
    
    # Get version history
    versions = supabase.table("template_versions").select(
        "id, version_number, change_log, created_at, created_by"
    ).eq("template_id", template_id).order("version_number", desc=True).execute()
    
    return {
        **template.data,
        "version_history": versions.data
    }

@router.patch("/{template_id}")
async def update_template(
    template_id: str,
    updates: TemplateUpdate,
    supabase=Depends(get_supabase_client),
    user=Depends(get_current_user)
):
    """Update template with versioning"""
    # Get current template
    current = supabase.table("context_templates").select("*").eq("id", template_id).single().execute()
    
    if not current.data:
        raise HTTPException(404, "Template not found")
    
    # Prepare update
    update_data = updates.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Update template
    result = supabase.table("context_templates").update(update_data).eq("id", template_id).execute()
    
    # Create new version if settings changed
    settings_changed = any(k in update_data for k in [
        "script_structure", "tone_settings", "islamic_guidelines", 
        "character_preferences", "voice_preferences"
    ])
    
    if settings_changed:
        # Get latest version number
        latest = supabase.table("template_versions").select("version_number").eq(
            "template_id", template_id
        ).order("version_number", desc=True).limit(1).execute()
        
        new_version = (latest.data[0]["version_number"] if latest.data else 0) + 1
        
        # Save version snapshot
        supabase.table("template_versions").insert({
            "template_id": template_id,
            "version_number": new_version,
            "settings_snapshot": {**current.data, **update_data},
            "change_log": f"Updated by {user.id}",
            "created_by": user.id
        }).execute()
    
    return result.data[0]

@router.post("/{template_id}/apply")
async def apply_template(
    template_id: str,
    override_settings: Optional[dict] = None,
    supabase=Depends(get_supabase_client)
):
    """Apply template to generate new video"""
    # Get template
    template = supabase.table("context_templates").select("*").eq("id", template_id).single().execute()
    
    if not template.data:
        raise HTTPException(404, "Template not found")
    
    # Increment usage count
    supabase.table("context_templates").update({
        "usage_count": template.data["usage_count"] + 1,
        "last_used_at": datetime.utcnow().isoformat()
    }).eq("id", template_id).execute()
    
    # Prepare generation config
    config = {
        "character_name": template.data["default_character"],
        "character_preferences": template.data["character_preferences"],
        "script_structure": template.data["script_structure"],
        "tone_settings": template.data["tone_settings"],
        "language_code": template.data["language_code"],
        "voice_preferences": template.data["voice_preferences"],
        "islamic_guidelines": template.data["islamic_guidelines"],
        "output_settings": template.data["output_settings"],
    }
    
    # Apply overrides
    if override_settings:
        config.update(override_settings)
    
    return {
        "template_applied": True,
        "generation_config": config,
        "template_name": template.data["name"]
    }

@router.delete("/{template_id}")
async def delete_template(template_id: str, supabase=Depends(get_supabase_client)):
    """Soft delete template"""
    result = supabase.table("context_templates").update(
        {"is_archived": True, "updated_at": datetime.utcnow().isoformat()}
    ).eq("id", template_id).execute()
    return {"success": True}

@router.get("/{template_id}/versions/{version_number}")
async def get_template_version(
    template_id: str,
    version_number: int,
    supabase=Depends(get_supabase_client)
):
    """Get specific version of template for rollback"""
    version = supabase.table("template_versions").select("*").eq(
        "template_id", template_id
    ).eq("version_number", version_number).single().execute()
    
    if not version.data:
        raise HTTPException(404, "Version not found")
    
    return version.data

@router.post("/{template_id}/rollback/{version_number}")
async def rollback_template(
    template_id: str,
    version_number: int,
    supabase=Depends(get_supabase_client),
    user=Depends(get_current_user)
):
    """Rollback template to previous version"""
    # Get version to rollback to
    target_version = supabase.table("template_versions").select("*").eq(
        "template_id", template_id
    ).eq("version_number", version_number).single().execute()
    
    if not target_version.data:
        raise HTTPException(404, "Version not found")
    
    # Get current template
    current = supabase.table("context_templates").select("*").eq("id", template_id).single().execute()
    
    # Update template with version settings
    settings = target_version.data["settings_snapshot"]
    update_data = {
        **settings,
        "updated_at": datetime.utcnow().isoformat(),
        "id": template_id  # Exclude ID from update
    }
    del update_data["id"]
    
    result = supabase.table("context_templates").update(update_data).eq("id", template_id).execute()
    
    # Log rollback as new version
    latest = supabase.table("template_versions").select("version_number").eq(
        "template_id", template_id
    ).order("version_number", desc=True).limit(1).execute()
    
    new_version = (latest.data[0]["version_number"] if latest.data else 0) + 1
    
    supabase.table("template_versions").insert({
        "template_id": template_id,
        "version_number": new_version,
        "settings_snapshot": result.data[0],
        "change_log": f"Rolled back to v{version_number} by {user.id}",
        "created_by": user.id
    }).execute()
    
    return {"success": True, "rolled_back_to": version_number}
```

---

## 🎨 **3. Frontend Components**

### **Video List Page (`static/pages/videos.html`):**

```html
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>📹 Islamic Video Library</title>
    <link rel="stylesheet" href="/static/css/dashboard.css">
    <link rel="stylesheet" href="/static/css/video-grid.css">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="logo">
                <h2>🕌 Babo Alert</h2>
            </div>
            <nav>
                <a href="/dashboard" class="nav-item">🏠 Dashboard</a>
                <a href="/videos" class="nav-item active">📹 Videos</a>
                <a href="/templates" class="nav-item">📋 Templates</a>
                <a href="/collections" class="nav-item">📚 Collections</a>
                <a href="/settings" class="nav-item">⚙️ Settings</a>
            </nav>
            
            <!-- Quick Filters -->
            <div class="quick-filters">
                <h4>🔍 Filter Videos</h4>
                <select id="filterContentType">
                    <option value="">All Types</option>
                    <option value="quran">📖 Quran</option>
                    <option value="hadith">📜 Hadith</option>
                    <option value="reminder">⚠️ Warnings</option>
                    <option value="story">📚 Stories</option>
                </select>
                <select id="filterCharacter">
                    <option value="">All Characters</option>
                    <option value="Sheikh Ahmad Al-Thai">🧔 Sheikh Ahmad</option>
                    <option value="Omar Young Muslim">👦 Omar</option>
                    <option value="Sister Aisha">🧕 Sister Aisha</option>
                </select>
                <select id="filterStatus">
                    <option value="">All Status</option>
                    <option value="completed">✅ Completed</option>
                    <option value="processing">🔄 Processing</option>
                    <option value="failed">❌ Failed</option>
                </select>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Header -->
            <header class="page-header">
                <h1>📹 Generated Videos</h1>
                <div class="header-actions">
                    <div class="search-box">
                        <input type="text" id="videoSearch" placeholder="🔍 Search videos...">
                        <button id="searchBtn">🔍</button>
                    </div>
                    <button id="newVideoBtn" class="btn-primary">
                        ➕ Create New Video
                    </button>
                </div>
            </header>

            <!-- Stats Cards -->
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number" id="totalVideos">0</span>
                    <span class="stat-label">Total Videos</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="totalViews">0</span>
                    <span class="stat-label">Total Views</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="avgDuration">0m</span>
                    <span class="stat-label">Avg Duration</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="favoriteCount">0</span>
                    <span class="stat-label">Favorites</span>
                </div>
            </div>

            <!-- Video Grid -->
            <div class="video-grid" id="videoGrid">
                <!-- Videos will be loaded here -->
            </div>

            <!-- Pagination -->
            <div class="pagination" id="pagination">
                <!-- Pagination controls -->
            </div>
        </main>
    </div>

    <!-- Video Card Template -->
    <template id="videoCardTemplate">
        <div class="video-card" data-video-id="">
            <div class="video-thumbnail">
                <img src="" alt="Thumbnail">
                <div class="video-overlay">
                    <span class="duration">8:00</span>
                    <span class="status-badge processing">🔄 Processing</span>
                </div>
                <button class="favorite-btn" title="Add to favorites">⭐</button>
            </div>
            <div class="video-info">
                <h3 class="video-title">Video Title</h3>
                <p class="video-desc">Short description...</p>
                <div class="video-meta">
                    <span class="meta-item">📖 Al-Baqarah:255</span>
                    <span class="meta-item">🧔 Sheikh Ahmad</span>
                </div>
                <div class="video-tags">
                    <span class="tag">warnings</span>
                    <span class="tag">hellfire</span>
                </div>
                <div class="video-actions">
                    <button class="btn-icon play-btn" title="Preview">▶️</button>
                    <button class="btn-icon edit-btn" title="Edit Settings">✏️</button>
                    <button class="btn-icon regenerate-btn" title="Regenerate">🔄</button>
                    <button class="btn-icon download-btn" title="Download">⬇️</button>
                    <button class="btn-icon more-btn" title="More">⋮</button>
                </div>
            </div>
        </div>
    </template>

    <!-- Edit Context Modal -->
    <div class="modal" id="editContextModal">
        <div class="modal-content modal-lg">
            <div class="modal-header">
                <h3>✏️ Edit Context Settings</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="contextEditForm">
                    <!-- Tab Navigation -->
                    <div class="form-tabs">
                        <button type="button" class="tab-btn active" data-tab="content">📝 Content</button>
                        <button type="button" class="tab-btn" data-tab="character">👤 Character</button>
                        <button type="button" class="tab-btn" data-tab="voice">🔊 Voice</button>
                        <button type="button" class="tab-btn" data-tab="output">🎬 Output</button>
                        <button type="button" class="tab-btn" data-tab="islamic">🕌 Islamic</button>
                    </div>

                    <!-- Content Tab -->
                    <div class="tab-content active" id="tab-content">
                        <div class="form-group">
                            <label>Quran/Hadith Reference *</label>
                            <input type="text" name="verse_reference" placeholder="e.g., Al-Baqarah:255">
                        </div>
                        <div class="form-group">
                            <label>Topic Category</label>
                            <select name="topic_category">
                                <option value="warnings">⚠️ Warnings & Reminders</option>
                                <option value="mercy">💚 Mercy & Hope</option>
                                <option value="guidance">🧭 Guidance & Practice</option>
                                <option value="stories">📚 Prophetic Stories</option>
                                <option value="aqidah">📖 Aqidah & Belief</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Script Structure</label>
                            <div class="script-structure-editor">
                                <!-- Visual editor for 7-clip structure -->
                                <div class="structure-item" data-section="hook">
                                    <span>🎣 Hook (0:00-0:15)</span>
                                    <textarea name="hook_prompt" rows="2"></textarea>
                                </div>
                                <!-- More sections... -->
                            </div>
                        </div>
                    </div>

                    <!-- Character Tab -->
                    <div class="tab-content" id="tab-character">
                        <div class="form-group">
                            <label>Character Model</label>
                            <div class="character-selector">
                                <div class="character-option selected" data-char="sheikh">
                                    <img src="/static/chars/sheikh.jpg">
                                    <span>Sheikh Ahmad</span>
                                </div>
                                <div class="character-option" data-char="omar">
                                    <img src="/static/chars/omar.jpg">
                                    <span>Omar Youth</span>
                                </div>
                                <div class="character-option" data-char="aisha">
                                    <img src="/static/chars/aisha.jpg">
                                    <span>Sister Aisha</span>
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Character Appearance</label>
                            <div class="appearance-options">
                                <label><input type="checkbox" name="beard" checked> Beard</label>
                                <label><input type="checkbox" name="thobe" checked> Traditional Thobe</label>
                                <label><input type="checkbox" name="hijab"> Hijab (for female)</label>
                            </div>
                        </div>
                    </div>

                    <!-- Voice Tab -->
                    <div class="tab-content" id="tab-voice">
                        <div class="form-group">
                            <label>Voice Model</label>
                            <select name="voice_id">
                                <option value="">Use Character Default</option>
                                <option value="scholar_deep">🧔 Scholar Deep</option>
                                <option value="youth_energetic">👦 Youth Energetic</option>
                                <option value="gentle_reminder">💚 Gentle Reminder</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Voice Settings</label>
                            <div class="voice-settings">
                                <label>Stability: <span id="stabilityVal">75</span>%</label>
                                <input type="range" name="voice_stability" min="0" max="100" value="75">
                                
                                <label>Similarity: <span id="similarityVal">85</span>%</label>
                                <input type="range" name="voice_similarity" min="0" max="100" value="85">
                                
                                <label>Style: <span id="styleVal">35</span>%</label>
                                <input type="range" name="voice_style" min="0" max="100" value="35">
                            </div>
                        </div>
                    </div>

                    <!-- Islamic Guidelines Tab -->
                    <div class="tab-content" id="tab-islamic">
                        <div class="form-group">
                            <label>Reference Sources</label>
                            <div class="source-checkboxes">
                                <label><input type="checkbox" name="sources[]" value="quran_sahih" checked> Quran (Sahih Intl)</label>
                                <label><input type="checkbox" name="sources[]" value="bukhari" checked> Sahih Bukhari</label>
                                <label><input type="checkbox" name="sources[]" value="muslim" checked> Sahih Muslim</label>
                                <label><input type="checkbox" name="sources[]" value="ibn_kathir"> Tafsir Ibn Kathir</label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Tone & Style</label>
                            <div class="tone-sliders">
                                <label>Seriousness: <span id="seriousVal">70</span>%</label>
                                <input type="range" name="tone_serious" min="0" max="100" value="70">
                                
                                <label>Mercy: <span id="mercyVal">80</span>%</label>
                                <input type="range" name="tone_mercy" min="0" max="100" value="80">
                                
                                <label>Urgency: <span id="urgencyVal">60</span>%</label>
                                <input type="range" name="tone_urgency" min="0" max="100" value="60">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Topics to Avoid</label>
                            <input type="text" name="avoid_topics" placeholder="Comma-separated topics">
                            <small>e.g., politics, sectarian issues</small>
                        </div>
                    </div>

                    <!-- Output Tab -->
                    <div class="tab-content" id="tab-output">
                        <div class="form-group">
                            <label>Video Format</label>
                            <select name="output_format">
                                <option value="1080p">1080p (Recommended)</option>
                                <option value="720p">720p (Faster)</option>
                                <option value="4k">4K (Premium)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Watermark</label>
                            <label><input type="checkbox" name="add_watermark" checked> Add Islamic watermark</label>
                        </div>
                        <div class="form-group">
                            <label>Auto-publish</label>
                            <label><input type="checkbox" name="auto_publish"> Publish to YouTube after generation</label>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn-secondary modal-close">Cancel</button>
                <button type="button" class="btn-primary" id="saveContextBtn">💾 Save Changes</button>
                <button type="button" class="btn-warning" id="saveAsTemplateBtn">📋 Save as Template</button>
            </div>
        </div>
    </div>

    <script src="/static/js/videos.js"></script>
</body>
</html>
```

### **JavaScript for Video Management (`static/js/videos.js`):**

```javascript
// Video List Management
class VideoManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.filters = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadVideos();
        this.loadStats();
    }

    bindEvents() {
        // Search
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.filters.search_query = document.getElementById('videoSearch').value;
            this.currentPage = 1;
            this.loadVideos();
        });

        // Filters
        document.getElementById('filterContentType').addEventListener('change', (e) => {
            this.filters.content_type = e.target.value || null;
            this.currentPage = 1;
            this.loadVideos();
        });

        // Video actions (delegation)
        document.getElementById('videoGrid').addEventListener('click', (e) => {
            const card = e.target.closest('.video-card');
            if (!card) return;

            const videoId = card.dataset.videoId;

            if (e.target.closest('.edit-btn')) {
                this.openEditModal(videoId);
            } else if (e.target.closest('.regenerate-btn')) {
                this.regenerateVideo(videoId);
            } else if (e.target.closest('.favorite-btn')) {
                this.toggleFavorite(videoId, card);
            } else if (e.target.closest('.play-btn')) {
                this.previewVideo(videoId);
            }
        });

        // Modal
        document.getElementById('saveContextBtn').addEventListener('click', () => {
            this.saveContextChanges();
        });
        document.getElementById('saveAsTemplateBtn').addEventListener('click', () => {
            this.saveAsTemplate();
        });
    }

    async loadVideos() {
        const params = new URLSearchParams({
            page: this.currentPage,
            per_page: this.perPage,
            ...this.filters
        });

        const response = await fetch(`/api/videos?${params}`);
        const data = await response.json();

        this.renderVideos(data.videos);
        this.renderPagination(data);
        this.updateStats(data);
    }

    renderVideos(videos) {
        const grid = document.getElementById('videoGrid');
        const template = document.getElementById('videoCardTemplate');
        
        grid.innerHTML = '';

        videos.forEach(video => {
            const card = template.content.cloneNode(true);
            const cardEl = card.querySelector('.video-card');
            
            cardEl.dataset.videoId = video.id;
            cardEl.querySelector('.video-thumbnail img').src = video.thumbnail_url || '/static/placeholder.jpg';
            cardEl.querySelector('.video-title').textContent = video.title;
            cardEl.querySelector('.video-desc').textContent = video.description?.substring(0, 100) + '...';
            cardEl.querySelector('.meta-item:first-child').textContent = video.verse_reference || '📜 Hadith';
            cardEl.querySelector('.meta-item:last-child').textContent = video.character_name || '👤 Generic';
            
            // Tags
            const tagsContainer = cardEl.querySelector('.video-tags');
            tagsContainer.innerHTML = '';
            (video.tags || []).slice(0, 3).forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = tag;
                tagsContainer.appendChild(tagEl);
            });

            // Status badge
            const statusBadge = cardEl.querySelector('.status-badge');
            statusBadge.className = `status-badge ${video.status}`;
            statusBadge.textContent = {
                'processing': '🔄 Processing',
                'completed': '✅ Completed',
                'failed': '❌ Failed'
            }[video.status] || video.status;

            // Favorite state
            if (video.is_favorite) {
                cardEl.querySelector('.favorite-btn').classList.add('active');
            }

            grid.appendChild(card);
        });
    }

    async openEditModal(videoId) {
        // Fetch video details
        const response = await fetch(`/api/videos/${videoId}`);
        const video = await response.json();

        // Populate form
        const form = document.getElementById('contextEditForm');
        
        // Content tab
        form.querySelector('[name="verse_reference"]').value = video.verse_reference || '';
        form.querySelector('[name="topic_category"]').value = video.topic_category || '';
        
        // Character tab
        if (video.character_name) {
            document.querySelectorAll('.character-option').forEach(opt => {
                opt.classList.remove('selected');
                if (opt.dataset.char === video.character_name.toLowerCase().split(' ')[0]) {
                    opt.classList.add('selected');
                }
            });
        }
        
        // Voice tab
        if (video.generation_config?.voice_preferences) {
            const vp = video.generation_config.voice_preferences;
            form.querySelector('[name="voice_stability"]').value = vp.stability * 100 || 75;
            form.querySelector('[name="voice_similarity"]').value = vp.similarity_boost * 100 || 85;
            form.querySelector('[name="voice_style"]').value = vp.style * 100 || 35;
        }

        // Islamic tab
        if (video.generation_config?.islamic_guidelines) {
            const guides = video.generation_config.islamic_guidelines;
            if (guides.sources) {
                guides.sources.forEach(src => {
                    const checkbox = form.querySelector(`[name="sources[]"][value="${src}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            }
        }

        // Store video ID for saving
        form.dataset.videoId = videoId;

        // Show modal
        document.getElementById('editContextModal').classList.add('active');
    }

    async saveContextChanges() {
        const form = document.getElementById('contextEditForm');
        const videoId = form.dataset.videoId;
        
        // Gather form data
        const updates = {
            verse_reference: form.querySelector('[name="verse_reference"]').value,
            topic_category: form.querySelector('[name="topic_category"]').value,
            generation_config: {
                character_preferences: {
                    beard: form.querySelector('[name="beard"]').checked,
                    thobe: form.querySelector('[name="thobe"]').checked,
                },
                voice_preferences: {
                    stability: form.querySelector('[name="voice_stability"]').value / 100,
                    similarity_boost: form.querySelector('[name="voice_similarity"]').value / 100,
                    style: form.querySelector('[name="voice_style"]').value / 100,
                },
                islamic_guidelines: {
                    sources: Array.from(form.querySelectorAll('[name="sources[]"]:checked'))
                        .map(cb => cb.value),
                    tone: {
                        seriousness: form.querySelector('[name="tone_serious"]').value / 100,
                        mercy: form.querySelector('[name="tone_mercy"]').value / 100,
                        urgency: form.querySelector('[name="tone_urgency"]').value / 100,
                    }
                }
            }
        };

        const response = await fetch(`/api/videos/${videoId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates)
        });

        if (response.ok) {
            alert('✅ Context settings saved!');
            document.getElementById('editContextModal').classList.remove('active');
            this.loadVideos(); // Refresh list
        } else {
            alert('❌ Failed to save changes');
        }
    }

    async saveAsTemplate() {
        const form = document.getElementById('contextEditForm');
        const templateName = prompt('📋 Enter template name:');
        
        if (!templateName) return;

        const templateData = {
            name: templateName,
            description: `Template created from video context`,
            content_type: form.querySelector('[name="topic_category"]').value || 'reminder',
            topic_category: form.querySelector('[name="topic_category"]').value,
            default_character: document.querySelector('.character-option.selected')?.dataset.char,
            character_preferences: {
                beard: form.querySelector('[name="beard"]').checked,
                thobe: form.querySelector('[name="thobe"]').checked,
            },
            voice_preferences: {
                stability: form.querySelector('[name="voice_stability"]').value / 100,
                similarity_boost: form.querySelector('[name="voice_similarity"]').value / 100,
                style: form.querySelector('[name="voice_style"]').value / 100,
            },
            islamic_guidelines: {
                sources: Array.from(form.querySelectorAll('[name="sources[]"]:checked'))
                    .map(cb => cb.value),
                tone: {
                    seriousness: form.querySelector('[name="tone_serious"]').value / 100,
                    mercy: form.querySelector('[name="tone_mercy"]').value / 100,
                    urgency: form.querySelector('[name="tone_urgency"]').value / 100,
                }
            },
            tags: ['custom', 'user-created']
        };

        const response = await fetch('/api/templates', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(templateData)
        });

        if (response.ok) {
            alert('🎉 Template saved successfully!');
        } else {
            alert('❌ Failed to save template');
        }
    }

    async regenerateVideo(videoId) {
        if (!confirm('🔄 Regenerate this video with current settings?')) return;

        const response = await fetch(`/api/videos/${videoId}/regenerate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        if (response.ok) {
            const result = await response.json();
            alert(`✅ Regeneration queued! Job ID: ${result.job_id}`);
            this.loadVideos();
        } else {
            alert('❌ Failed to queue regeneration');
        }
    }

    async toggleFavorite(videoId, card) {
        const btn = card.querySelector('.favorite-btn');
        const isFavorite = btn.classList.toggle('active');

        await fetch(`/api/videos/${videoId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({is_favorite: isFavorite})
        });
    }

    renderPagination(data) {
        const pagination = document.getElementById('pagination');
        // ... pagination rendering logic
    }

    async loadStats() {
        // Load dashboard stats
        const response = await fetch('/api/videos/stats');
        const stats = await response.json();
        
        document.getElementById('totalVideos').textContent = stats.total;
        document.getElementById('totalViews').textContent = stats.total_views?.toLocaleString() || '0';
        document.getElementById('avgDuration').textContent = `${Math.round(stats.avg_duration / 60)}m`;
        document.getElementById('favoriteCount').textContent = stats.favorites;
    }

    updateStats(data) {
        // Update stats from list response if needed
    }

    previewVideo(videoId) {
        // Open video player modal
        window.open(`/videos/${videoId}/preview`, '_blank');
    }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoManager();
});
```

---

## 📋 **4. Template Management Page (`static/pages/templates.html`):**

```html
<!-- Template List Page Structure -->
<div class="template-grid" id="templateGrid">
    <!-- System Templates -->
    <div class="template-section">
        <h3>🏛️ System Templates</h3>
        <div class="template-cards">
            <div class="template-card system" data-template-id="quran-warning">
                <div class="template-icon">⚠️</div>
                <h4>Quran Warning Series</h4>
                <p>โครงสร้างสำหรับเตือนใจจากอัลกุรอาน</p>
                <div class="template-meta">
                    <span>📖 Quran</span>
                    <span>🧔 Sheikh Ahmad</span>
                </div>
                <button class="btn-use-template">Use Template</button>
                <button class="btn-edit-template">✏️</button>
            </div>
            <!-- More system templates... -->
        </div>
    </div>

    <!-- User Templates -->
    <div class="template-section">
        <h3>📁 My Templates 
            <button id="newTemplateBtn" class="btn-sm">➕ New</button>
        </h3>
        <div class="template-cards" id="userTemplates">
            <!-- User templates loaded dynamically -->
        </div>
    </div>
</div>

<!-- Template Detail Modal -->
<div class="modal" id="templateDetailModal">
    <div class="modal-content modal-xl">
        <div class="modal-header">
            <h3>📋 Template: <span id="templateName"></span></h3>
            <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Version History -->
            <div class="version-history">
                <h4>📜 Version History</h4>
                <div class="versions-list" id="versionsList">
                    <!-- Versions loaded dynamically -->
                </div>
                <button id="rollbackBtn" class="btn-warning">🔄 Rollback to Selected</button>
            </div>

            <!-- Settings Preview -->
            <div class="settings-preview">
                <h4>⚙️ Current Settings</h4>
                <pre id="settingsJson"></pre>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary modal-close">Close</button>
            <button class="btn-primary" id="applyTemplateBtn">🚀 Apply & Generate</button>
        </div>
    </div>
</div>
```

---

## 🔍 **5. Smart Features Implementation**

### **Smart Search & Filtering (`utils/search.py`):**

```python
class IslamicVideoSearch:
    """Advanced search for Islamic video content"""
    
    @staticmethod
    def build_search_query(
        search_term: str,
        content_type: str = None,
        tags: List[str] = None
    ) -> dict:
        """Build Elasticsearch-like query for Supabase"""
        
        query = {"filters": {}}
        
        # Full-text search with Islamic terms weighting
        if search_term:
            islamic_keywords = {
                "narak": "hellfire", "สวรรค์": "paradise", 
                "กลับตัว": "repentance", "กิยามะฮฺ": "judgment"
            }
            
            # Expand search with Islamic synonyms
            expanded_terms = [search_term]
            for th, en in islamic_keywords.items():
                if th in search_term.lower():
                    expanded_terms.append(en)
                if en in search_term.lower():
                    expanded_terms.append(th)
            
            query["search"] = " | ".join(expanded_terms)
            query["search_config"] = "thai"
        
        # Content type filter
        if content_type:
            query["filters"]["content_type"] = content_type
        
        # Tag filtering with hierarchy
        if tags:
            islamic_tag_hierarchy = {
                "warnings": ["hellfire", "judgment", "punishment"],
                "mercy": ["forgiveness", "paradise", "hope"],
                "guidance": ["prayer", "quran", "sunnah"]
            }
            
            expanded_tags = set(tags)
            for tag in tags:
                if tag in islamic_tag_hierarchy:
                    expanded_tags.update(islamic_tag_hierarchy[tag])
            
            query["filters"]["tags_overlap"] = list(expanded_tags)
        
        return query
    
    @staticmethod
    def rank_results(results: List[dict], user_preferences: dict) -> List[dict]:
        """Rank videos based on user behavior and Islamic relevance"""
        
        for video in results:
            score = 0
            
            # Preference matching
            if user_preferences.get("favorite_character") == video.get("character_name"):
                score += 20
            
            # Content relevance
            if user_preferences.get("preferred_topics"):
                video_tags = set(video.get("tags", []))
                pref_tags = set(user_preferences["preferred_topics"])
                score += len(video_tags & pref_tags) * 10
            
            # Engagement boost
            score += video.get("views_count", 0) * 0.01
            score += video.get("likes_count", 0) * 0.5
            
            # Recency boost
            from datetime import datetime, timedelta
            if video.get("created_at"):
                days_old = (datetime.utcnow() - video["created_at"]).days
                if days_old <= 7:
                    score += 15
                elif days_old <= 30:
                    score += 5
            
            video["relevance_score"] = score
        
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
```

### **Auto-Tagging System (`utils/auto_tagger.py`):**

```python
class IslamicAutoTagger:
    """Automatically tag Islamic content based on analysis"""
    
    ISLAMIC_KEYWORDS = {
        "hellfire": ["นรก", "fire", "punishment", "jahannam"],
        "paradise": ["สวรรค์", "jannah", "reward", "gardens"],
        "repentance": ["กลับตัว", "taubah", "forgiveness", "istighfar"],
        "judgment": ["กิยามะฮฺ", "qiyamah", "accountability", "hisab"],
        "mercy": ["เมตตา", "rahmah", "forgiveness", "compassion"],
        "guidance": ["ฮิดายะฮฺ", "guidance", "straight path", "siratal mustaqim"],
        "patience": ["อดทน", "sabr", "perseverance"],
        "gratitude": ["ขอบคุณ", "shukr", "grateful"]
    }
    
    @classmethod
    def analyze_and_tag(cls, text: str, verse_ref: str = None) -> List[str]:
        """Analyze content and generate relevant tags"""
        tags = set()
        text_lower = text.lower()
        
        # Keyword matching
        for tag, keywords in cls.ISLAMIC_KEYWORDS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                tags.add(tag)
        
        # Verse-based tagging
        if verse_ref:
            verse_tags = cls._get_verse_tags(verse_ref)
            tags.update(verse_tags)
        
        # Content type detection
        if any(q in text_lower for q in ["อัลลอฮฺ", "الله", "allah"]):
            tags.add("quran_content")
        if any(h in text_lower for h in ["ท่านนบี", "ﷺ", "prophet"]):
            tags.add("hadith_content")
        
        # Emotional tone detection
        if any(w in text_lower for w in ["ระวัง", "เตือน", "warning", "fear"]):
            tags.add("warning_tone")
        if any(w in text_lower for w in ["หวัง", "hope", "mercy", "เมตตา"]):
            tags.add("hopeful_tone")
        
        return list(tags)
    
    @staticmethod
    def _get_verse_tags(verse_ref: str) -> List[str]:
        """Get predefined tags for Quran verses"""
        verse_tag_map = {
            "Al-Baqarah:255": ["ayat_al_kursi", "protection", "power_of_allah"],
            "Al-Imran:131-136": ["hellfire_warning", "repentance", "patience"],
            "Al-Asr:1-3": ["time_management", "good_deeds", "truth"],
            # Add more mappings
        }
        return verse_tag_map.get(verse_ref, [])
```

---

## 🗄️ **6. Database Migration Script**

```sql
-- migrations/002_add_video_template_system.sql

-- Run this to update your Supabase database

-- Add new columns to existing videos table if needed
ALTER TABLE generated_videos 
ADD COLUMN IF NOT EXISTS context_template_id UUID REFERENCES context_templates(id),
ADD COLUMN IF NOT EXISTS tags TEXT[],
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT false;

-- Create GIN indexes for JSONB and array searches
CREATE INDEX IF NOT EXISTS idx_videos_generation_config 
ON generated_videos USING gin(generation_config);

CREATE INDEX IF NOT EXISTS idx_templates_settings 
ON context_templates USING gin(character_preferences, tone_settings, islamic_guidelines);

-- Create function for full-text search with Islamic terms
CREATE OR REPLACE FUNCTION islamic_video_search(
    search_query TEXT,
    content_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
    id UUID,
    title TEXT,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.title,
        ts_rank(
            to_tsvector('thai', v.title || ' ' || COALESCE(v.description, '')),
            to_tsquery('thai', search_query)
        ) as relevance
    FROM generated_videos v
    WHERE v.is_archived = false
    AND (content_filter IS NULL OR v.content_type = content_filter)
    AND to_tsvector('thai', v.title || ' ' || COALESCE(v.description, ''))
        @@ to_tsquery('thai', search_query)
    ORDER BY relevance DESC;
END;
$$ LANGUAGE plpgsql;
```

---

## 🎯 **สรุปฟีเจอร์ที่เพิ่ม:**

### ✅ **ระบบจัดการวิดีโอ:**
- 📊 **Smart List**: แสดงวิดีโอแบบกริด พร้อมรูปปก, สถานะ, แท็ก
- 🔍 **Advanced Search**: ค้นหาด้วยคำสำคัญ, หมวดหมู่, ตัวละคร, แท็ก
- 🏷️ **Auto-Tagging**: ระบบติดแท็กอัตโนมัติตามเนื้อหาอิสลาม
- ⭐ **Favorites**: ปักหมุดวิดีโอที่ชอบ
- 📁 **Collections**: จัดกลุ่มวิดีโอเป็นซีรีส์/คอลเลกชัน

### ✏️ **ระบบแก้ไข Context:**
- 🎛️ **Tab-based Editor**: แก้ไขตั้งค่าแบบแยกแท็บ (Content/Character/Voice/Islamic/Output)
- 🎨 **Visual Script Editor**: แก้ไขโครงสร้าง 7 คลิปแบบเห็นภาพ
- 🎚️ **Voice Sliders**: ปรับความเสถียร/สไตล์เสียงแบบเรียลไทม์
- 🕌 **Islamic Guidelines**: ตั้งค่าแหล่งอ้างอิงและโทนเนื้อหา

### 📋 **ระบบ Template:**
- 💾 **Save as Template**: บันทึกการตั้งค่าเป็นเทมเพลตใช้ซ้ำ
- 📜 **Version History**: เก็บประวัติการแก้ไข ย้อนกลับได้
- 🔄 **One-Click Apply**: ใช้เทมเพลตสร้างวิดีโอใหม่ในคลิกเดียว
- 🌐 **Share Templates**: แชร์เทมเพลตในทีม (is_public)

### 🧠 **Smart Features:**
- 🎯 **Relevance Ranking**: จัดลำดับวิดีโอตามความสนใจผู้ใช้
- 🏷️ **Islamic Keyword Expansion**: ค้นหาด้วยคำอิสลามทั้งไทย/อังกฤษ/อาหรับ
- 📈 **Usage Analytics**: ติดตามว่าเทมเพลตไหนใช้บ่อยสุด
- 🔄 **Regenerate with Updates**: สร้างวิดีโอใหม่ด้วยการตั้งค่าที่อัปเดต

---

## 🚀 **ขั้นตอนการติดตั้ง:**

```bash
# 1. Update database
supabase db push migrations/002_add_video_template_system.sql

# 2. Add new routes to main.py
# ใน main.py เพิ่ม:
from routes import videos, templates
app.include_router(videos.router)
app.include_router(templates.router)

# 3. Add new static files
# วางไฟล์ใหม่ในโฟลเดอร์:
# - static/pages/videos.html
# - static/pages/templates.html  
# - static/css/video-grid.css
# - static/js/videos.js

# 4. Update requirements.txt (ถ้าใช้ฟีเจอร์ใหม่)
pip install python-multipart  # สำหรับ form uploads

# 5. Restart application
python main.py
```

ระบบนี้จะช่วยให้คุณจัดการเนื้อหาอิสลามได้อย่างเป็นมืออาชีพ มีระบบ และนำกลับมาใช้ซ้ำได้อย่างชาญฉลาด! 🕌✨

มีส่วนไหนต้องการให้อธิบายเพิ่มเติมหรือปรับแต่งเป็นพิเศษ บอกได้เลยนะครับ! 🚀