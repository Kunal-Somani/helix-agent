"""Authentication and authorization middleware."""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from passlib.context import CryptContext
from app.config import settings
import structlog

logger = structlog.get_logger()

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_api_key(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify API key from Authorization header."""
    token = credentials.credentials
    
    # In production, validate against database or secret manager
    if token != settings.MY_SECRET:
        logger.warning("invalid_api_key_attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    logger.info("api_key_verified")
    return token


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
