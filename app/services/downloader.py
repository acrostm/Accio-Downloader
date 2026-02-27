import os
import tempfile
import yt_dlp
from sqlalchemy.orm import Session
from app.schemas.video_schema import VideoFormat, ParseResponse

from typing import Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

from app.core.config import settings

def get_cookies_file_for_url() -> Optional[str]:
    # Check if a global COOKIES_FILE exists locally
    if os.path.exists(settings.COOKIES_FILE):
        return settings.COOKIES_FILE
    return None

def parse_video(url: str, db: Session) -> ParseResponse:
    ydl_opts = {
        'geo_bypass': True,
        'sleep_requests': 1.5,
        'http_headers': {
            'User-Agent': USER_AGENT
        },
        'quiet': True,
        'extract_flat': False
    }

    cookie_file = get_cookies_file_for_url()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail')
            formats_data = info.get('formats', [])
            
            formats = []
            for f in formats_data:
                # filter out audio only or dash formats that might not be standalone videos if needed
                # For simplicity, we just extract what we can
                if f.get('vcodec') != 'none': # has video
                    resolution = f.get('resolution') or f"{f.get('width', 'cell')}x{f.get('height', 'cell')}"
                    formats.append(VideoFormat(
                        format_id=f.get('format_id', ''),
                        resolution=resolution,
                        ext=f.get('ext', ''),
                        filesize=f.get('filesize')
                    ))
            
            # Sort formats by resolution height if possible (simple heuristic)
            # In a real app we might parse the height integer to sort
            
            return ParseResponse(
                title=title,
                thumbnail=thumbnail,
                formats=formats
            )
    except Exception as e:
        raise e

def download_video_sync(url: str, format_id: str, output_path: str, db: Session):
    ydl_opts = {
        'geo_bypass': True,
        'sleep_requests': 1.5,
        'format': format_id if format_id and format_id != 'best' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'http_headers': {
            'User-Agent': USER_AGENT
        },
        'quiet': False
    }
    
    cookie_file = get_cookies_file_for_url()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise e
