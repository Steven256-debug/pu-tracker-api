"""
Authentication. Streamlit kept role identity in server-side session state;
a stateless React+API architecture needs a real token instead. This issues
a short-lived JWT containing the role and faculty scope, which the frontend
stores and sends on every request. The backend re-derives faculty
restrictions from the token on every call — the frontend never decides
what a role is allowed to see, the backend always does.
"""
import os
import datetime
from typing import Optional

import jwt
from fastapi import HTTPException, Header

from .config import ROLES

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = 12


def _secret(key: str, fallback: str) -> str:
    return os.environ.get(key, fallback)


def verify_login(role: str, password: str) -> bool:
    cfg = ROLES.get(role)
    if not cfg:
        return False
    correct = _secret(cfg["pwd_key"], cfg["default"])
    return password == correct


def issue_token(role: str) -> str:
    cfg = ROLES[role]
    payload = {
        "role": role,
        "faculty": cfg["faculty"],
        "tabs": cfg["tabs"],
        "icon": cfg["icon"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session. Please sign in again.")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency — extracts and validates the bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_token(token)


def enforce_faculty_scope(user: dict, requested_faculty: Optional[str]) -> Optional[str]:
    """
    Returns the faculty the caller is actually allowed to query.
    A scoped role can never widen their own access by changing a request
    parameter — the backend always uses the token's faculty if the role
    is restricted, ignoring any wider value the client might send.
    """
    user_faculty = user.get("faculty")
    if user_faculty is None:
        # Dean of Students — unrestricted, may filter to any single faculty if requested
        return requested_faculty
    return user_faculty
