from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from models.base import Base

# Enum for user roles
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"

# SQLAlchemy User model for database
class User(Base):
    """Database User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    birth_date = Column(Date, nullable=True)
    grade_level = Column(Integer, nullable=True)
    role = Column(String, default=UserRole.STUDENT.value)
    is_active = Column(Boolean, default=True)
    disabled = Column(Boolean, default=False)
    
    # For parent-child relationship
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    children = relationship("User", 
                           backref="parent",
                           remote_side=[id])
    
    def filtered_dict(self, fields):
        """Convert User to dict with only specified fields."""
        result = {}
        for field in fields:
            if hasattr(self, field):
                result[field] = getattr(self, field)
        return result