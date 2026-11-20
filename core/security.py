from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt
from core.config import settings

MAX_BCRYPT_PASSWORD_BYTES = 72
# Precomputed dummy bcrypt hash used to equalize login response timing when user is absent
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"timing-fallback-dummy-secret", bcrypt.gensalt()).decode("utf-8")


def get_password_hash(password: str) -> str:
    """Hash a plain text password using bcrypt ($2b$)."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("Password exceeds bcrypt 72-byte limit.")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JSON Web Token (JWT) for user authentication."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
