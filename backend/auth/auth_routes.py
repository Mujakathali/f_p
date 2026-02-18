"""
Authentication Routes
Handles registration, login, and user profile endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict

from .dependencies import get_current_user
from .user_manager import UserManager

# Create router (prefix will be added in app.py)
auth_router = APIRouter(tags=["Authentication"])

# User manager will be initialized in app.py after postgres_db is created
user_manager = None


def initialize_auth(postgres_connection):
    """Initialize authentication system with database connection"""
    global user_manager
    user_manager = UserManager(postgres_connection)
    return user_manager


def _require_user_manager() -> UserManager:
    if user_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication system not initialized yet. Please retry in a moment."
        )
    return user_manager


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class AuthResponse(BaseModel):
    user: Dict
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    created_at: str
    last_login: Optional[str]


@auth_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user
    
    Request body:
    {
        "email": "user@example.com",
        "username": "johndoe",
        "password": "securepassword123",
        "full_name": "John Doe"  // optional
    }
    
    Returns:
    {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "created_at": "2024-01-01T00:00:00"
        },
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer"
    }
    """
    try:
        um = _require_user_manager()
        # Ensure users table exists
        await um.create_users_table()
        
        # Register user
        result = await um.register_user(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@auth_router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login user and get JWT token
    
    Request body:
    {
        "email_or_username": "johndoe",  // can be email or username
        "password": "securepassword123"
    }
    
    Returns:
    {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "full_name": "John Doe"
        },
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer"
    }
    """
    try:
        um = _require_user_manager()
        result = await um.login_user(
            email_or_username=request.email_or_username,
            password=request.password
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current user profile (protected route)
    
    Requires: Authorization header with Bearer token
    Header: Authorization: Bearer <token>
    
    Returns:
    {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-02T10:30:00"
    }
    """
    try:
        user = await user_manager.get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}"
        )


@auth_router.post("/verify")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    Verify if token is valid (protected route)
    
    Requires: Authorization header with Bearer token
    
    Returns:
    {
        "valid": true,
        "user_id": 1,
        "username": "johndoe"
    }
    """
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"]
    }
