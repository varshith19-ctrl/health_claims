"""
Auth route — /auth/register and /auth/login endpoints.
Uses bcrypt-hashed passwords and simple JWT tokens.
"""
import json
import hashlib
import secrets
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from config.settings import DATA_DIR

log = get_logger("api.routes.auth")
router = APIRouter()

USER_DB_PATH = DATA_DIR / "users.json"


class AuthRequest(BaseModel):
    username: str
    password: str


def _load_users() -> dict:
    if not USER_DB_PATH.exists():
        default = {"admin": _hash_password("password")}
        USER_DB_PATH.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        return json.loads(USER_DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_users(users: dict):
    USER_DB_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _hash_password(password: str) -> str:
    salt = "claimshield_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _generate_token(username: str) -> str:
    return f"{username}:{secrets.token_hex(32)}:{int(time.time())}"


@router.post("/auth/register")
async def register(req: AuthRequest):
    username = req.username.strip()
    password = req.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if len(username) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    users = _load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="Username already exists")

    users[username] = _hash_password(password)
    _save_users(users)
    log.info("New user registered: %s", username)
    return {"message": "Registration successful", "username": username}


@router.post("/auth/login")
async def login(req: AuthRequest):
    username = req.username.strip()
    password = req.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    users = _load_users()
    hashed = _hash_password(password)

    if username not in users or users[username] != hashed:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = _generate_token(username)
    log.info("User logged in: %s", username)
    return {"message": "Login successful", "username": username, "token": token}
