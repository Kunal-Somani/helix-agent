"""Authentication and authorization middleware.

Uses Bearer token authentication with HMAC constant-time comparison
to prevent timing attacks.
"""

import hmac

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.logger import log

security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Verify API key from Authorization header.
    
    Validates Bearer token using constant-time HMAC comparison
    to prevent timing attacks.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        The validated credentials string
        
    Raises:
        HTTPException: 401 if token is invalid
    """
    token = credentials.credentials

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(token, settings.MY_SECRET):
        log.warning("auth.invalid_api_key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    log.info("auth.verified")
    return token
