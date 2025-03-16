# sangram_tutor/models/base.py
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """Base model for all database models with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# sangram_tutor/models/user.py
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, Column, Enum as SQLAEnum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from sangram_tutor.models.base import BaseModel, Base


class UserRole(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING_WRITING = "reading_writing"
    KINESTHETIC = "kinesthetic"
    LOGICAL = "logical"
    SOCIAL = "social"
    SOLITARY = "solitary"


# Association table for many-to-many relationship between users and learning styles
user_learning_styles = Table(
    "user_learning_styles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("learning_style", SQLAEnum(LearningStyle)),
)


class User(BaseModel):
    """User model representing students, parents, and teachers."""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    
    # Profile information
    full_name = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)
    grade_level = Column(Integer, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    language_preference = Column(String(10), default="en")
    
    # Relationships
    learning_styles = relationship(
        "LearningStyle",
        secondary=user_learning_styles,
        backref="users"
    )
    progress = relationship("Progress", back_populates="user")
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    children = relationship("User", backref="parent", remote_side=[id])


# sangram_tutor/models/curriculum.py
from enum import Enum
from typing import List, Optional

from sqlalchemy import (Column, Enum as SQLAEnum, Float, ForeignKey, Integer, 
                       String, Table, Text)
from sqlalchemy.orm import relationship

from sangram_tutor.models.base import BaseModel, Base


class Subject(str, Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE = "language"
    SOCIAL_STUDIES = "social_studies"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ContentType(str, Enum):
    CONCEPT = "concept"
    EXAMPLE = "example" 
    EXERCISE = "exercise"
    GAME = "game"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"


# Association table for prerequisites
content_prerequisites = Table(
    "content_prerequisites",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("curriculum_content.id")),
    Column("prerequisite_id", Integer, ForeignKey("curriculum_content.id"))
)


class CurriculumTopic(BaseModel):
    """Model representing a curriculum topic based on NCERT syllabus."""
    __tablename__ = "curriculum_topics"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(SQLAEnum(Subject), nullable=False, default=Subject.MATHEMATICS)
    grade_level = Column(Integer, nullable=False)
    standard_code = Column(String(50), nullable=True)  # NCERT standard code
    
    # Relationships
    contents = relationship("CurriculumContent", back_populates="topic")


class CurriculumContent(BaseModel):
    """Model representing specific content items within a topic."""
    __tablename__ = "curriculum_content"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_data = Column(Text, nullable=False)  # JSON content data
    content_type = Column(SQLAEnum(ContentType), nullable=False)
    difficulty_level = Column(SQLAEnum(DifficultyLevel), nullable=False)
    estimated_time_minutes = Column(Integer, default=10)
    points_reward = Column(Integer, default=10)
    
    # Foreign Keys
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"), nullable=False)
    
    # Relationships
    topic = relationship("CurriculumTopic", back_populates="contents")
    prerequisites = relationship(
        "CurriculumContent",
        secondary=content_prerequisites,
        primaryjoin=(content_prerequisites.c.content_id == id),
        secondaryjoin=(content_prerequisites.c.prerequisite_id == id),
        backref="dependent_contents"
    )
    progress = relationship("Progress", back_populates="content")


# sangram_tutor/models/progress.py
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (Column, DateTime, Enum as SQLAEnum, Float, ForeignKey, 
                       Integer, String, Boolean, Text)
from sqlalchemy.orm import relationship

from sangram_tutor.models.base import BaseModel


class CompletionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MASTERED = "mastered"


class Progress(BaseModel):
    """Model tracking student progress on curriculum content."""
    __tablename__ = "progress"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("curriculum_content.id"), nullable=False)
    
    # Progress data
    status = Column(SQLAEnum(CompletionStatus), default=CompletionStatus.NOT_STARTED)
    score = Column(Float, nullable=True)
    attempts = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Learning data
    confidence_level = Column(Float, nullable=True)  # AI-assessed confidence (0-1)
    mistakes_data = Column(Text, nullable=True)  # JSON data about patterns of mistakes
    engagement_score = Column(Float, nullable=True)  # Measure of user engagement (0-1)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    content = relationship("CurriculumContent", back_populates="progress")


# sangram_tutor/models/achievements.py
from enum import Enum
from typing import List, Optional

from sqlalchemy import (Column, Enum as SQLAEnum, ForeignKey, Integer, 
                       String, Table, Text, DateTime)
from sqlalchemy.orm import relationship

from sangram_tutor.models.base import BaseModel, Base


class AchievementType(str, Enum):
    COMPLETION = "completion"  # Completing a number of exercises
    MASTERY = "mastery"        # Mastering a topic
    STREAK = "streak"          # Daily login streak
    SPEED = "speed"            # Completing exercises quickly
    ACCURACY = "accuracy"      # High accuracy in answers
    PERSISTENCE = "persistence"  # Overcoming challenges
    EXPLORATION = "exploration"  # Trying new topics/features


# Association table for user achievements
user_achievements = Table(
    "user_achievements",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("achievement_id", Integer, ForeignKey("achievements.id")),
    Column("earned_at", DateTime),
)


class Achievement(BaseModel):
    """Model for defining achievements that students can earn."""
    __tablename__ = "achievements"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    achievement_type = Column(SQLAEnum(AchievementType), nullable=False)
    icon_url = Column(String(255), nullable=True)
    points_value = Column(Integer, default=10)
    requirement_data = Column(Text, nullable=False)  # JSON with requirements
    
    # Relationships through association table
    users = relationship(
        "User",
        secondary=user_achievements,
        backref="achievements"
    )
