from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import video
from app.models.base import Base
from app.api.dependencies import engine
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
import os

from sqlalchemy import text
from app.api.dependencies import engine

# Create the database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Auto-migration for SQLite to inject new columns
with engine.begin() as conn:
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN thumbnail VARCHAR;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN percent INTEGER;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN downloaded_bytes INTEGER;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN total_bytes INTEGER;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN speed_str VARCHAR;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN eta_str VARCHAR;"))
        except Exception: pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN format_note VARCHAR;"))
        except Exception: pass

app = FastAPI(title="Accio-Downloader")

# Load CORS origins from env (comma-separated)
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router, prefix="/api/v1/video", tags=["Video"])

# Mount downloads directory for local file access
os.makedirs(settings.TEMP_DOWNLOAD_DIR, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=settings.TEMP_DOWNLOAD_DIR), name="downloads")
