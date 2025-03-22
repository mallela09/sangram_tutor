from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

# Create the router object
router = APIRouter(prefix="/auth", tags=["authentication"])

# Define a simple User model for auth purposes
class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "student"
    grade_level: Optional[int] = None
    is_active: bool = True

    class Config:
        orm_mode = True

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current authenticated user from a JWT token.
    This is a placeholder implementation.
    """
    # In a real implementation, this would verify the token
    # and fetch the user from the database
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="student",
        grade_level=3,
        is_active=True
    )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Dependency to ensure a user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user

@router.get("/")
async def auth_root():
    """Basic endpoint to test that the auth API is working."""
    return {"message": "Auth API is working"}

@router.post("/token")
async def login_for_access_token():
    """
    Authenticate user and return JWT token.
    
    This is a placeholder. Actual implementation would validate 
    credentials and return a token.
    """
    return {
        "access_token": "dummy_token",
        "token_type": "bearer",
        "user_id": 1,
        "username": "dummy_user",
        "role": "student"
    }