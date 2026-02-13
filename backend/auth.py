"""
JWT Authentication Module for Marine Routing System
Handles user registration, login, password hashing, and token verification.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import os

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "marine-routing-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============ Pydantic Models ============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    created_at: str


# ============ Password Utilities ============

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============ JWT Token Utilities ============

def create_access_token(user_id: str, email: str, username: str) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: The user's database ID
        email: User's email
        username: User's username
        
    Returns:
        The encoded JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token string to decode
        
    Returns:
        The decoded payload dictionary if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============ JWT Bearer Authentication ============

class JWTBearer(HTTPBearer):
    """
    Custom HTTPBearer that validates JWT tokens.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Dict[str, Any]:
        """
        Extract and validate the token from the request.
        """
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            
            payload = decode_token(credentials.credentials)
            
            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return payload
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization credentials"
        )


# Dependency for protected routes
jwt_bearer = JWTBearer()


async def get_current_user(payload: Dict[str, Any] = Depends(jwt_bearer)) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    Use this as a dependency for protected routes.
    """
    return payload
