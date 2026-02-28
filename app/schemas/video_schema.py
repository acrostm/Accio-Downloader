from pydantic import BaseModel, validator
from typing import List, Optional, Any
import re

class VideoFormat(BaseModel):
    format_id: str
    resolution: Optional[str] = None
    ext: str
    filesize: Optional[int] = None

class ParseRequest(BaseModel):
    url: str

class ParseResponse(BaseModel):
    title: str
    thumbnail: Optional[str] = None
    formats: List[VideoFormat] = []

class DownloadRequest(BaseModel):
    url: Any  # Allow Any to normalize iOS Shortcuts list inputs
    format_id: Optional[str] = "best"

    @validator('url', pre=True)
    def extract_url(cls, v):
        raw_str = str(v[0]) if (isinstance(v, list) and len(v) > 0) else str(v)
        # Use regex to extract the first valid HTTP/HTTPS URL (strips iOS share junk)
        match = re.search(r'(https?://[^\s]+)', raw_str)
        if match:
            return match.group(1)
        return raw_str

class DownloadResponse(BaseModel):
    task_id: str
    status: str

class TaskResponse(BaseModel):
    id: str
    url: str
    title: Optional[str] = None
    status: str
    format_id: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: str
    local_url: Optional[str] = None
    
    thumbnail: Optional[str] = None
    percent: Optional[int] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed_str: Optional[str] = None
    eta_str: Optional[str] = None
    format_note: Optional[str] = None

    class Config:
        from_attributes = True
