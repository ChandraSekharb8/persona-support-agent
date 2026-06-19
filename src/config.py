import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Root project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Knowledge base folder
DATA_DIR = BASE_DIR / "data"

# ChromaDB persistent storage folder
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Gemini API Key from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini models
# Gemini models
GENERATION_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

# RAG settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

# Escalation settings
CONFIDENCE_THRESHOLD = 0.45

# Sensitive keywords that should trigger human escalation
SENSITIVE_KEYWORDS = [
    "refund",
    "billing",
    "duplicate charge",
    "legal",
    "unauthorized payment",
    "account ownership",
    "tax",
    "lawsuit",
    "chargeback",
    "data breach",
    "security breach"
]