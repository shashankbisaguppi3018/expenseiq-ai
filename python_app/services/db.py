"""Database and configuration helpers."""
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "expenseiq_py")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_client = MongoClient(MONGO_URL)
db = _client[DB_NAME]

CATEGORIES = [
    "Food", "Shopping", "Rent", "Transport", "Utilities",
    "Entertainment", "Healthcare", "Education", "Investments", "Miscellaneous",
]


def format_inr(amount: float) -> str:
    try:
        return f"₹{float(amount):,.0f}"
    except Exception:
        return "₹0"
