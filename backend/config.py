import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_RACE_MODELS = os.getenv("LLM_RACE_MODELS", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Deploy
NETLIFY_TOKEN = os.getenv("NETLIFY_TOKEN", "")

# Auth
JWT_SECRET = os.getenv("JWT_SECRET", "atoms-mvp-dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
DB_PATH = os.path.join(DATA_DIR, "atoms.db")

os.makedirs(PROJECTS_DIR, exist_ok=True)