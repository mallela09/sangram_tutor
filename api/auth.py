from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

# Import from models package
from models import User, UserRole

# Configure detailed logging
logger = logging.getLogger(__name__)

# Create the router object
router = APIRouter(prefix="/auth", tags=["authentication"])

# Define a token response model
class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user from token."""
    try:
        # In a real implementation, verify the token and fetch user from DB
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.STUDENT.value,
            grade_level=3,
            is_active=True,
            disabled=False,
            hashed_password="dummy_hashed_password"
        )
        logger.debug(f"Created user: {user.username} with full_name: {user.full_name}")
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Ensure user is active."""
    if current_user.disabled or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Authenticate user and return JWT token."""
    logger.debug(f"Token requested for username: {form_data.username}")
    
    # Create token response
    token_response = {
        "access_token": "dummy_token",
        "token_type": "bearer",
        "user_id": 1,
        "username": form_data.username,
        "role": "student"
    }
    
    logger.debug(f"Returning token: {token_response}")
    return token_response

@router.get("/")
async def auth_root():
    """Basic endpoint to test that the auth API is working."""
    return {"message": "Auth API is working"}