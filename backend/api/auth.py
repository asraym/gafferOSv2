import os
import hmac
import time
import base64
import hashlib
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "coach")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")
AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret")


class LoginRequest(BaseModel):
    username: str
    password: str


def sign_token(username: str) -> str:
    expires = int(time.time()) + 60 * 60 * 24 * 7
    payload = f"{username}:{expires}"
    sig = hmac.new(
        AUTH_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_token(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, expires, sig = raw.split(":")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = f"{username}:{expires}"
    expected = hmac.new(
        AUTH_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="Invalid token")

    if int(expires) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return username


def require_auth(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.removeprefix("Bearer ").strip()
    return verify_token(token)


@router.post("/auth/login")
def login(req: LoginRequest):
    if not AUTH_PASSWORD:
        raise HTTPException(status_code=500, detail="AUTH_PASSWORD not configured")

    if req.username != AUTH_USERNAME or req.password != AUTH_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "token": sign_token(req.username),
        "username": req.username,
    }


@router.get("/auth/me")
def me(username: str = None):
    return {"status": "ok"}