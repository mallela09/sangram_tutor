from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from api.auth import get_current_active_user, User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"], prefix="/users")

# Dummy user database for this example
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Wonderland",
        "disabled": False,
    },
    "bob": {
        "username": "bob",
        "email": "bob@example.com",
        "full_name": "Bob Builder",
        "disabled": True,
    }
}

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = Field(default=None)
    password: str

    class Config:
        populate_by_name = True
        extra = "ignore"

class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)

    class Config:
        populate_by_name = True
        extra = "ignore"

class UserOut(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)
    
    class Config:
        populate_by_name = True
        extra = "ignore"

# Helper function to safely convert between models
def safe_user_conversion(user: Any, output_model: Any) -> Any:
    """Safely convert a user object to the specified output model."""
    try:
        # Extract only the fields that exist in the output model
        fields = output_model.__annotations__.keys()
        user_dict = {}
        
        # Handle User model from auth.py
        if hasattr(user, "filtered_dict"):
            user_dict = user.filtered_dict(fields)
        # Handle dictionary user data
        elif isinstance(user, dict):
            user_dict = {k: v for k, v in user.items() if k in fields}
        # Handle any other object by getting attributes
        else:
            for field in fields:
                if hasattr(user, field):
                    user_dict[field] = getattr(user, field)
        
        # Ensure required fields are present
        if "username" not in user_dict and hasattr(user, "username"):
            user_dict["username"] = user.username
            
        # Create and return the output model instance
        return output_model(**user_dict)
    except Exception as e:
        logger.error(f"Error converting user: {e}")
        # Return a default instance if conversion fails
        default_values = {field: None for field in output_model.__annotations__}
        if "username" in output_model.__annotations__:
            default_values["username"] = "error_user"
        if "email" in output_model.__annotations__:
            default_values["email"] = "error@example.com"
        return output_model(**default_values)

@router.get("/", response_model=List[UserOut])
async def read_users(current_user: User = Depends(get_current_active_user)):
    """Get a list of all users."""
    try:
        users_list = []
        for username, user_data in fake_users_db.items():
            # Create a dictionary with all needed fields
            user_dict = {**user_data, "username": username}
            # Convert to UserOut using safe conversion
            user_out = safe_user_conversion(user_dict, UserOut)
            users_list.append(user_out)
        return users_list
    except Exception as e:
        logger.error(f"Error in read_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get information about the current authenticated user."""
    try:
        # Use safe conversion to handle any potential field mismatches
        return safe_user_conversion(current_user, UserOut)
    except Exception as e:
        logger.error(f"Error in read_users_me: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )

@router.get("/{username}", response_model=UserOut)
async def read_user(username: str, current_user: User = Depends(get_current_active_user)):
    """Get a specific user by username."""
    try:
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} not found"
            )
        
        # Create a completely new dictionary with required fields
        user_dict = {**fake_users_db[username], "username": username}
        
        # Use safe conversion
        return safe_user_conversion(user_dict, UserOut)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in read_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user)):
    """Create a new user."""
    try:
        if user.username in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username {user.username} already exists"
            )
        
        # Convert to dict and handle fields explicitly
        user_data = user.model_dump(exclude_unset=True)
        username = user_data.pop("username")
        password = user_data.pop("password")
        
        # Set disabled flag
        user_data["disabled"] = False
        
        # Store in database
        fake_users_db[username] = user_data
        
        # Prepare response with username included
        response_data = {**user_data, "username": username}
        
        # Use safe conversion to return
        return safe_user_conversion(response_data, UserOut)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.put("/{username}", response_model=UserOut)
async def update_user(
    username: str, 
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Update a user's information."""
    try:
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} not found"
            )
        
        # Get existing user data
        user_data = fake_users_db[username].copy()
        
        # Get update data, excluding unset fields
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Apply updates
        for key, value in update_data.items():
            if value is not None:
                user_data[key] = value
        
        # Save updated data
        fake_users_db[username] = user_data
        
        # Prepare response with username included
        response_data = {**user_data, "username": username}
        
        # Use safe conversion to return
        return safe_user_conversion(response_data, UserOut)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str, current_user: User = Depends(get_current_active_user)):
    """Delete a user."""
    try:
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} not found"
            )
        
        # Delete user
        del fake_users_db[username]
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )