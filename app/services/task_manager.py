import os
import re
import shutil
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.base import Task, TaskStatus
from app.services.downloader import download_video_sync
from app.core.config import settings


def detect_platform(url: str) -> str:
    """Detect the video platform from the URL and return a display folder name."""
    url_lower = url.lower()
    platforms = {
        "bilibili.com": "bilibili",
        "b23.tv": "bilibili",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "tiktok.com": "tiktok",
        "douyin.com": "douyin",
        "xiaohongshu.com": "xiaohongshu",
        "xhslink.com": "xiaohongshu",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "instagram.com": "instagram",
        "weibo.com": "weibo",
        "v.qq.com": "tencent-video",
        "iqiyi.com": "iqiyi",
        "youku.com": "youku",
        "twitch.tv": "twitch",
        "nicovideo.jp": "nicovideo",
    }
    for domain, name in platforms.items():
        if domain in url_lower:
            return name
    return "other"


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """Remove filesystem-unsafe characters and truncate long titles."""
    if not name:
        return "video"
    # Remove illegal filename characters
    safe = re.sub(r'[\\/*?:"<>|]', '', name)
    # Replace newlines and tabs with spaces
    safe = re.sub(r'[\n\r\t]+', ' ', safe)
    # Collapse multiple spaces
    safe = re.sub(r' {2,}', ' ', safe).strip()
    # Truncate
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip()
    return safe or "video"


def organize_download(url: str, title: str, raw_file_path: str) -> str:
    """
    Move the downloaded file from the temp location to an organized folder:
        TEMP_DOWNLOAD_DIR / platform / YYYY-MM-DD / sanitized_title.ext
    Returns the final file path.
    """
    ext = os.path.splitext(raw_file_path)[1]  # e.g. ".mp4"
    platform = detect_platform(url)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title)

    final_dir = os.path.join(settings.TEMP_DOWNLOAD_DIR, platform, date_str)
    os.makedirs(final_dir, exist_ok=True)

    # Avoid filename collisions
    final_path = os.path.join(final_dir, f"{safe_title}{ext}")
    if os.path.exists(final_path):
        ts = datetime.utcnow().strftime("%H%M%S")
        final_path = os.path.join(final_dir, f"{safe_title}_{ts}{ext}")

    shutil.move(raw_file_path, final_path)
    return final_path


def process_download_task(task_id: str, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return

    try:
        # Step 1: Downloading
        task.status = TaskStatus.DOWNLOADING
        db.commit()

        # Use a unique temp filename based on task_id to avoid collisions
        temp_filename = f"{task_id}.%(ext)s"
        temp_output_template = os.path.join(settings.TEMP_DOWNLOAD_DIR, temp_filename)

        download_video_sync(task.url, task.format_id, temp_output_template, db)

        # Find the actual downloaded file (yt-dlp adds the real extension)
        actual_files = [
            f for f in os.listdir(settings.TEMP_DOWNLOAD_DIR)
            if f.startswith(task_id) and os.path.isfile(os.path.join(settings.TEMP_DOWNLOAD_DIR, f))
        ]
        if not actual_files:
            raise Exception("Downloaded file not found after yt-dlp execution")

        raw_path = os.path.join(settings.TEMP_DOWNLOAD_DIR, actual_files[0])

        # Step 2: Move to organized folder
        title = task.title or "video"
        final_path = organize_download(task.url, title, raw_path)

        task.local_path = final_path
        task.status = TaskStatus.COMPLETED
        db.commit()

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_msg = str(e)
        db.commit()
