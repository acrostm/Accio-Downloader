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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
