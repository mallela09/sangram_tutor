from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base

# Learning progress model
class LearningProgress(Base):
    """Model for tracking user progress on content items."""
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_id = Column(Integer, ForeignKey("curriculum_contents.id"))
    
    # Completion status
    started_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Performance tracking
    attempts = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    
    # Detailed performance data
    answers_data = Column(Text, nullable=True)  # JSON stored as text
    mistakes_data = Column(Text, nullable=True)  # JSON stored as text
    
    # Engagement metrics
    engagement_score = Column(Float, nullable=True)
    
    # Feedback
    user_rating = Column(Integer, nullable=True)
    user_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="progress_items")
    content = relationship("CurriculumContent", backref="user_progress")

# Topic progress model (aggregates content progress for a topic)
class TopicProgress(Base):
    """Model for tracking user progress on curriculum topics."""
    __tablename__ = "topic_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"))
    
    # Aggregated metrics
    started_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    completion_percentage = Column(Float, default=0.0)
    average_score = Column(Float, nullable=True)
    total_time_spent_seconds = Column(Integer, default=0)
    mastery_level = Column(Integer, default=0)  # 0-5 scale
    
    # Relationships
    user = relationship("User", backref="topic_progress")
    topic = relationship("CurriculumTopic", backref="user_progress")

# Learning session model (tracks individual learning sessions)
class LearningSession(Base):
    """Model for tracking individual learning sessions."""
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Session timing
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # Session metrics
    items_completed = Column(Integer, default=0)
    points_earned = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)
    
    # Device and context
    device_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Session metadata
    session_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", backref="learning_sessions")
    
    # Add relationship to track what content was completed in this session
    content_items = relationship(
        "LearningProgress",
        secondary="session_progress",
        backref="sessions"
    )

# Association table for session-progress relationship
class SessionProgress(Base):
    """Links learning sessions with progress items."""
    __tablename__ = "session_progress"
    
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), primary_key=True)
    progress_id = Column(Integer, ForeignKey("learning_progress.id"), primary_key=True)