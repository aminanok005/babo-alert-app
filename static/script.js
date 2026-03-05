let currentJobId = null;
let pollInterval = null;

async function generateClips() {
    const verseRef = document.getElementById('verseRef').value;
    const topic = document.getElementById('topic').value;
    
    if (!verseRef) {
        alert('กรุณาใส่อ้างอิงอายะฮ์');
        return;
    }
    
    // Disable button
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = '⏳ กำลังสร้าง...';
    
    // Show progress section
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Initialize workflow steps
    initWorkflowSteps();
    
    try {
        // Start generation
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verse_reference: verseRef, topic: topic })
        });
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start polling
        pollInterval = setInterval(pollStatus, 2000);
        
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
        btn.disabled = false;
        btn.textContent = '🎬 Generate 7 คลิป';
    }
}

async function pollStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        const data = await response.json();
        
        // Update progress bar
        const progress = (data.completed / data.total_clips) * 100;
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = `${data.completed}/${data.total_clips} คลิป`;
        
        // Update workflow steps
        updateWorkflowSteps(data.clips);
        
        // Check if completed
        if (data.status === 'completed') {
            clearInterval(pollInterval);
            showResults(data.clips);
            
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🎬 Generate 7 คลิป';
        } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            alert('การสร้างคลิปล้มเหลว: ' + data.error);
            btn.disabled = false;
            btn.textContent = '🎬 Generate 7 คลิป';
        }
        
    } catch (error) {
        console.error('Polling error:', error);
    }
}

function initWorkflowSteps() {
    const container = document.getElementById('workflowSteps');
    container.innerHTML = '';
    
    const steps = [
        { icon: '📝', text: 'สร้างสคริปต์จาก AI' },
        { icon: '✂️', text: 'แบ่งเป็น 7 ส่วน' },
        { icon: '🎙️', text: 'สร้างเสียง (TTS)' },
        { icon: '🎬', text: 'เรนเดอร์วิดีโอ' },
        { icon: '💾', text: 'บันทึกไฟล์' },
        { icon: '📤', text: 'พร้อมใช้งาน' }
    ];
    
    steps.forEach((step, index) => {
        const stepEl = document.createElement('div');
        stepEl.className = 'step';
        stepEl.id = `step-${index}`;
        stepEl.innerHTML = `
            <span class="step-icon">${step.icon}</span>
            <div class="step-text">
                <div>${step.text}</div>
                <div class="step-status">รอ...</div>
            </div>
        `;
        container.appendChild(stepEl);
    });
}

function updateWorkflowSteps(clips) {
    const completed = clips.filter(c => c.status === 'completed').length;
    const totalSteps = 6;
    
    for (let i = 0; i < totalSteps; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        const statusEl = stepEl.querySelector('.step-status');
        
        if (i < completed) {
            stepEl.className = 'step completed';
            statusEl.textContent = '✓ เสร็จ';
        } else if (i === completed) {
            stepEl.className = 'step active';
            statusEl.textContent = '⏳ กำลังทำ...';
        } else {
            stepEl.className = 'step';
            statusEl.textContent = 'รอ...';
        }
    }
}

function showResults(clips) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    const grid = document.getElementById('clipsGrid');
    grid.innerHTML = '';
    
    clips.forEach(clip => {
        const card = document.createElement('div');
        card.className = 'clip-card';
        card.innerHTML = `
            <h3>คลิปที่ ${clip.clip_number}</h3>
            <video controls>
                <source src="${clip.video_url}" type="video/mp4">
                เบราว์เซอร์ไม่รองรับวิดีโอ
            </video>
            <div class="clip-actions">
                <button class="btn-download" onclick="downloadClip(${clip.clip_number})">
                    ⬇️ ดาวน์โหลด
                </button>
                <button class="btn-share" onclick="shareClip(${clip.clip_number})">
                    🔗 แชร์
                </button>
                <button class="btn-upload" onclick="uploadClip(${clip.clip_number})">
                    📺 YouTube
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

async function downloadClip(clipNumber) {
    window.open(`/api/download/${currentJobId}/${clipNumber}`, '_blank');
}

async function shareClip(clipNumber) {
    const url = `${window.location.origin}/api/download/${currentJobId}/${clipNumber}`;
    
    if (navigator.share) {
        await navigator.share({
            title: `Quran Clip ${clipNumber}`,
            url: url
        });
    } else {
        await navigator.clipboard.writeText(url);
        alert('ลิงก์ถูกคัดลอกแล้ว!');
    }
}

async function uploadClip(clipNumber) {
    try {
        const response = await fetch(`/api/upload/${currentJobId}/${clipNumber}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`อัพโหลดสำเร็จ! ${data.youtube_url}`);
        } else {
            alert('อัพโหลดล้มเหลว');
        }
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

// เพิ่มในส่วนท้ายของ script.js

async function showContext(type) {
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Load context content
    try {
        const response = await fetch(`/api/context/${type}`);
        const data = await response.json();
        document.getElementById('contextContent').textContent = data.content;
    } catch (error) {
        document.getElementById('contextContent').textContent = 'โหลดข้อมูลไม่สำเร็จ';
    }
}

// โหลด Context เริ่มต้น
document.addEventListener('DOMContentLoaded', () => {
    showContext('memory');
});