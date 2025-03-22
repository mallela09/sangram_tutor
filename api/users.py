from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from api.auth import get_current_active_user, User

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
    full_name: Optional[str] = None
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserOut(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

@router.get("/", response_model=List[UserOut])
async def read_users(current_user: User = Depends(get_current_active_user)):
    """Get a list of all users."""
    return [UserOut(**user) for user in fake_users_db.values()]

@router.get("/{username}", response_model=UserOut)
async def read_user(username: str, current_user: User = Depends(get_current_active_user)):
    """Get a specific user by username."""
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    return UserOut(**fake_users_db[username])

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user)):
    """Create a new user."""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username {user.username} already exists"
        )
    
    # In a real app, you would hash the password here
    user_data = user.dict()
    password = user_data.pop("password")  # Don't store password in user data
    user_data["disabled"] = False
    
    fake_users_db[user.username] = user_data
    return UserOut(**user_data)

@router.put("/{username}", response_model=UserOut)
async def update_user(
    username: str, 
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Update a user's information."""
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    
    user_data = fake_users_db[username]
    update_data = user_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            user_data[key] = value
    
    fake_users_db[username] = user_data
    return UserOut(**user_data)

@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str, current_user: User = Depends(get_current_active_user)):
    """Delete a user."""
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    
    del fake_users_db[username]
    return None



