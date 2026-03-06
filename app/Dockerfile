# app/Dockerfile
FROM python:3.11-slim

# ติดตั้ง dependencies ของระบบ
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง IBM Plex Sans Thai font
RUN mkdir -p /usr/share/fonts/truetype/ibm-plex && \
    curl -L -o /usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Regular.ttf \
    "https://github.com/IBM/plex/raw/master/fonts/IBM-Plex-Sans-Thai/IBMPlexSansThai-Regular.ttf" && \
    curl -L -o /usr/share/fonts/truetype/ibm-plex/IBMPlexSansThai-Bold.ttf \
    "https://github.com/IBM/plex/raw/master/fonts/IBM-Plex-Sans-Thai/IBMPlexSansThai-Bold.ttf" && \
    fc-cache -fv

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
