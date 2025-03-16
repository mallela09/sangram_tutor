# sangram_tutor/utils/security.py
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from sangram_tutor.models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "temporarysecretkeyfordevonly")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain password matches a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: Dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# sangram_tutor/utils/auth.py
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from sangram_tutor.db.session import get_db
from sangram_tutor.models.user import User
from sangram_tutor.utils.security import SECRET_KEY, ALGORITHM

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from a JWT token.
    
    Args:
        token: JWT token from the request
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
        
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure a user is active.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The authenticated active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


# sangram_tutor/utils/permissions.py
from enum import Enum
from typing import List, Optional

from fastapi import Depends, HTTPException, status

from sangram_tutor.models.user import User, UserRole
from sangram_tutor.utils.auth import get_current_active_user


class Permission(str, Enum):
    """Enum for permission types."""
    READ_CONTENT = "read_content"
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"
    ADMIN_ACCESS = "admin_access"


# Role-based permissions
ROLE_PERMISSIONS = {
    UserRole.STUDENT: [
        Permission.READ_CONTENT
    ],
    UserRole.PARENT: [
        Permission.READ_CONTENT,
        Permission.VIEW_ANALYTICS
    ],
    UserRole.TEACHER: [
        Permission.READ_CONTENT,
        Permission.CREATE_CONTENT,
        Permission.EDIT_CONTENT,
        Permission.VIEW_ANALYTICS
    ],
    UserRole.ADMIN: [
        Permission.READ_CONTENT,
        Permission.CREATE_CONTENT,
        Permission.EDIT_CONTENT,
        Permission.DELETE_CONTENT,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_USERS,
        Permission.ADMIN_ACCESS
    ]
}


def has_permission(permission: Permission, user: User) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        permission: The permission to check
        user: The user to check permissions for
        
    Returns:
        True if the user has the permission, False otherwise
    """
    if not user:
        return False
        
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def require_permission(permission: Permission):
    """
    Dependency function factory to require a specific permission.
    
    Args:
        permission: The required permission
        
    Returns:
        Dependency function that validates the permission
    """
    def dependency(current_user: User = Depends(get_current_active_user)):
        if not has_permission(permission, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    
    return dependency
