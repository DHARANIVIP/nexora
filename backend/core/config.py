import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent / '.env')

class Settings:
    PROJECT_NAME: str = "Deepfake Defense System"
    VERSION: str = "2.0 (Advanced)"
    
    # Dynamic Path Setup
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR = BASE_DIR / "storage"
    
    # New scan-based storage structure
    SCANS_FOLDER = STORAGE_DIR / "scans"
    
    # Allowed Video Formats
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    # Database
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://vvdharani57_db_user:GPRXbgUnuzy9FSnW@cluster0.tnkfodr.mongodb.net/?appName=Cluster0")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "sentinel_ai")

settings = Settings()

# Auto-create directories on start
settings.SCANS_FOLDER.mkdir(parents=True, exist_ok=True)