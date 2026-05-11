import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / "backend" / ".env"

load_dotenv(ENV_PATH)


BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в backend/.env")