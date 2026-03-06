import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

async def upload_to_youtube(file_path, title):
    # ต้องตั้งค่า OAuth2 credentials ก่อน
    # ดู: https://developers.google.com/youtube/v3/guides/uploading_a_video
    return "https://youtube.com/watch?v=xxx"  # Placeholder