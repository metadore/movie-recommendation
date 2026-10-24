import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import database
from models import users_table

JWT_SECRET = os.getenv("JWT_SECRET", "cinepulse-dev-secret-change-me-32b+")
JWT_ALG = "HS256"
JWT_HOURS = 72
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password hashing – bcrypt (salted, work factor 12)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*.  The salt is embedded in the hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def verify_password(password: str, stored: str) -> bool:
    """Verify *password* against a bcrypt *stored* hash.

    Also handles the old PBKDF2 format (``salt$hexdigest``) so existing
    accounts keep working until their next login.
    """
    # Legacy PBKDF2 format kept for backward-compatibility
    if "$2b$" not in stored and "$2a$" not in stored and "$2y$" not in stored:
        import hashlib

        try:
            salt, digest = stored.split("$", 1)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
        ).hex()
        return secrets.compare_digest(check, digest)

    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: int, username: str, role: str = "user", mfa_verified: bool = False
) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "mfa_verified": mfa_verified,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


# ---------------------------------------------------------------------------
# TOTP helpers
# ---------------------------------------------------------------------------

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username, issuer_name="CinePulse"
    )


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ---------------------------------------------------------------------------
# FastAPI dependency helpers
# ---------------------------------------------------------------------------

async def _decode_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict | None:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALG]
        )
        return payload
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    payload = await _decode_token(credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    user_id = int(payload["sub"])
    user = await database.fetch_one(
        users_table.select().where(users_table.c.id == user_id)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    result = dict(user)
    result["role"] = payload.get("role", "user")
    result["mfa_verified"] = payload.get("mfa_verified", False)
    return result


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(*roles: str):
    """Dependency factory – raises 403 if the user's role is not in *roles*."""

    async def _check(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.get('role')}' is not allowed. Required: {list(roles)}",
            )
        return user

    return _check
