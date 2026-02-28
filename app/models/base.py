from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    url = Column(String, index=True)
    title = Column(String, nullable=True)
    status = Column(String, default=TaskStatus.PENDING, index=True)
    format_id = Column(String, nullable=True)
    local_path = Column(String, nullable=True)
    error_msg = Column(String, nullable=True)
    
    # Progress & Metadata
    thumbnail = Column(String, nullable=True)
    percent = Column(Integer, nullable=True) # 0 to 100
    downloaded_bytes = Column(Integer, nullable=True)
    total_bytes = Column(Integer, nullable=True)
    speed_str = Column(String, nullable=True)
    eta_str = Column(String, nullable=True)
    format_note = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
