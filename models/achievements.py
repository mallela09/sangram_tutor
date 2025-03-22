from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Table, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from models.base import Base

# Enum for achievement types
class AchievementType(str, enum.Enum):
    COMPLETION = "completion"
    STREAK = "streak"
    MASTERY = "mastery"
    TIME = "time"
    BADGE = "badge"
    CERTIFICATE = "certificate"
    PROGRESS = "progress"
    SPECIAL = "special"

# Association table for achievement prerequisites
achievement_prerequisites = Table(
    "achievement_prerequisites",
    Base.metadata,
    Column("achievement_id", Integer, ForeignKey("achievements.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("achievements.id"), primary_key=True)
)

# Achievement model
class Achievement(Base):
    """Model for achievements and badges."""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    achievement_type = Column(Enum(AchievementType))
    
    # Achievement criteria and rewards
    points_reward = Column(Integer, default=0)
    requirement_count = Column(Integer, default=1)  # e.g., complete 5 quizzes
    requirement_type = Column(String)  # e.g., "topic_completion", "consecutive_days"
    requirement_subject = Column(String, nullable=True)  # Optional subject requirement
    
    # Visual elements
    icon_url = Column(String, nullable=True)
    badge_url = Column(String, nullable=True)
    
    # Achievement rarity/difficulty
    difficulty = Column(Integer, default=1)  # 1-5 scale
    is_hidden = Column(Boolean, default=False)  # Secret achievements
    
    # Relationships
    prerequisites = relationship(
        "Achievement",
        secondary=achievement_prerequisites,
        primaryjoin=id==achievement_prerequisites.c.achievement_id,
        secondaryjoin=id==achievement_prerequisites.c.prerequisite_id,
        backref="unlocks"
    )

# User achievement model (tracks which users have earned which achievements)
class UserAchievement(Base):
    """Model for tracking user achievements."""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    
    # When it was earned
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional tracking information
    progress_value = Column(Integer, default=0)  # For partially completed achievements
    is_displayed = Column(Boolean, default=True)  # If user displays this on profile
    
    # Relationships
    user = relationship("User", backref="achievements")
    achievement = relationship("Achievement")