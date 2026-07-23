"""
Authentication — JWT token creation/verification and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Returns payload or raises."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI dependency: extract user_id from JWT token."""
    try:
        payload = verify_token(credentials.credentials)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")