import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
MODEL_DIR = BASE_DIR / "models"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

WHISPER_MODEL = "small.bin"
WHISPER_MODEL_PATH = MODEL_DIR / WHISPER_MODEL

WHISPER_CONFIG = {
    "model": str(WHISPER_MODEL_PATH),
    "language": "auto",  # Changed from "en" to "auto" for Filipino/Taglish support
    "threads": 8,
    "processors": 4,
    "output_format": "txt",
    "vad_thold": 0.4,
    "no_timestamps": False
}

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {".m4a", ".mp3", ".wav", ".aac", ".mp4"}

CLEANUP_INTERVAL = 3600  # Clean temp files every hour
MAX_CONCURRENT_JOBS = 2  # Number of files to process in parallel