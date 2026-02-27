from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./sql_app.db", env="DATABASE_URL")

    PORT: int = Field(default=8000, env="PORT")

    # Path to local cookies.txt (Netscape format, yt-dlp compatible)
    COOKIES_FILE: str = Field(default="./cookies.txt", env="COOKIES_FILE")

    # Directory where downloaded videos are organized
    TEMP_DOWNLOAD_DIR: str = Field(default="./downloads", env="TEMP_DOWNLOAD_DIR")

    # Comma-separated list of allowed CORS origins
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="CORS_ORIGINS"
    )

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure download dir exists
os.makedirs(settings.TEMP_DOWNLOAD_DIR, exist_ok=True)
