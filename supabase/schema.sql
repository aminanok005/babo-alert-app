-- supabase/schema.sql
-- รันใน Supabase SQL Editor

-- ===== ตารางโปรเจกต์ =====
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    verse_reference TEXT NOT NULL,
    topic TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    user_id UUID
);

-- ===== ตารางคลิป =====
CREATE TABLE IF NOT EXISTS clips (
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
CREATE TABLE IF NOT EXISTS social_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- youtube, telegram, facebook, tiktok
    platform_id TEXT,
    platform_url TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== Indexes สำหรับความเร็ว =====
CREATE INDEX IF NOT EXISTS idx_clips_project ON clips(project_id);
CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(status);
CREATE INDEX IF NOT EXISTS idx_social_uploads_clip ON social_uploads(clip_id);
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);

-- ===== Enable RLS =====
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_uploads ENABLE ROW LEVEL SECURITY;

-- Allow public read/write for now (can be restricted later)
CREATE POLICY "Allow all access to projects" ON projects FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to clips" ON clips FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to social_uploads" ON social_uploads FOR ALL USING (true) WITH CHECK (true);
