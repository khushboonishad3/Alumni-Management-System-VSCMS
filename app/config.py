import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "CMS Kanpur BCA/MCA Alumni Technical Networking Platform"
    PROJECT_VERSION: str = "1.0.0"
    COLLEGE_NAME: str = "Dr. Virendra Swarup College of Management Studies (CMS Kanpur)"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database - Default to SQLite for immediate local execution, or PostgreSQL via DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/cms_alumni.db")
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cms-kanpur-bca-mca-super-secret-jwt-key-2025-secure-hash")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 24 hours
    
    # Media & Storage (Use /tmp on serverless environments like Vercel)
    MEDIA_DIR: Path = Path("/tmp/media") if os.getenv("VERCEL") else BASE_DIR / "media"
    AVATARS_DIR: Path = MEDIA_DIR / "avatars"
    RESUMES_DIR: Path = MEDIA_DIR / "resumes"
    RESOURCES_DIR: Path = MEDIA_DIR / "resources"
    PROJECT_FILES_DIR: Path = MEDIA_DIR / "projects"
    
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_IMAGE_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    ALLOWED_RESUME_EXTENSIONS: set = {".pdf", ".docx", ".doc"}
    ALLOWED_RESOURCE_EXTENSIONS: set = {".pdf", ".docx", ".zip", ".tar.gz", ".py", ".java", ".cpp", ".ipynb", ".sql", ".txt", ".md"}

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "*"
    ]

settings = Settings()

# Ensure directories exist safely without failing on read-only environments
for folder in [settings.MEDIA_DIR, settings.AVATARS_DIR, settings.RESUMES_DIR, settings.RESOURCES_DIR, settings.PROJECT_FILES_DIR]:
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        pass
