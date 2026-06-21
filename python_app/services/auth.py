"""Email/password authentication using bcrypt + JWT."""
import bcrypt
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from services.db import db, JWT_SECRET


def _now():
    return datetime.now(timezone.utc)


def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def verify_password(pwd: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pwd.encode(), hashed.encode())
    except Exception:
        return False


def create_jwt(user_id: str) -> str:
    payload = {"sub": user_id, "exp": _now() + timedelta(days=7), "iat": _now()}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


def signup(email: str, password: str, name: str):
    email = email.strip().lower()
    if db.users.find_one({"email": email}):
        return None, "Email already registered"
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    db.users.insert_one({
        "user_id": user_id, "email": email, "name": name,
        "password_hash": hash_password(password),
        "created_at": _now().isoformat(),
    })
    db.budgets.insert_one({
        "user_id": user_id, "global_limit": 20000.0,
        "categories": {"Food": 5000, "Shopping": 3000, "Transport": 2000, "Utilities": 1500},
    })
    token = create_jwt(user_id)
    return {"user_id": user_id, "email": email, "name": name, "token": token}, None


def login(email: str, password: str):
    user = db.users.find_one({"email": email.strip().lower()})
    if not user or not verify_password(password, user.get("password_hash", "")):
        return None, "Invalid credentials"
    token = create_jwt(user["user_id"])
    return {"user_id": user["user_id"], "email": user["email"], "name": user["name"], "token": token}, None


def get_user_by_id(user_id: str):
    return db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})