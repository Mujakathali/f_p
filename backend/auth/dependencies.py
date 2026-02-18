"""
FastAPI Dependencies for Authentication
Middleware and dependency injection for protected routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import asyncio

from .jwt_handler import jwt_handler
from db.postgresql_connector import PostgreSQLConnector

# Security scheme
security = HTTPBearer()

# Simple shared connector for token revocation checks
_auth_pg = PostgreSQLConnector()
_pg_ready = False


async def _ensure_pg():
    global _pg_ready
    if not _pg_ready:
        await _auth_pg.connect()
        _pg_ready = True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current authenticated user from JWT token
    
    Usage in routes:
        @router.get("/protected")
        async def protected_route(current_user: Dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"]}
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    payload = jwt_handler.decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check revocation via shared connector
    await _ensure_pg()
    jti = payload.get("jti")
    if jti and await _auth_pg.is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    Optional authentication - returns user if token provided, None otherwise
    
    Usage in routes:
        @router.get("/optional-auth")
        async def optional_route(current_user: Optional[Dict] = Depends(get_optional_user)):
            if current_user:
                return {"message": f"Hello {current_user['username']}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = jwt_handler.decode_token(token)
    
    return payload
