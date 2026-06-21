"""Database and configuration helpers."""
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import streamlit as st

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

def get_config(name, default=""):
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


MONGO_URL = get_config("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = get_config("DB_NAME", "expenseiq_py")
JWT_SECRET = get_config("JWT_SECRET", "dev-secret-change-me")
EMERGENT_LLM_KEY = get_config("EMERGENT_LLM_KEY", "")
GEMINI_API_KEY = get_config("GEMINI_API_KEY", "")

_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000)
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
