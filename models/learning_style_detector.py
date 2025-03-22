from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base

# Learning style model
class LearningStyle(Base):
    """Model for storing user learning style profiles."""
    __tablename__ = "learning_styles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Core learning style dimensions (VARK model with extensions)
    visual_score = Column(Float, default=0.0)  # Visual learning preference
    auditory_score = Column(Float, default=0.0)  # Auditory learning preference
    reading_writing_score = Column(Float, default=0.0)  # Reading/writing preference
    kinesthetic_score = Column(Float, default=0.0)  # Hands-on learning preference
    
    # Additional dimensions
    logical_score = Column(Float, default=0.0)  # Logical/mathematical preference
    social_score = Column(Float, default=0.0)  # Group learning preference
    solitary_score = Column(Float, default=0.0)  # Independent learning preference
    
    # Analysis metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)  # Confidence in the assessment
    
    # Raw interaction data used for calculation
    interaction_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", backref="learning_style")

# Learning interaction model (stores data for learning style analysis)
class LearningInteraction(Base):
    """Model for tracking interactions used to determine learning style."""
    __tablename__ = "learning_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_id = Column(Integer, ForeignKey("curriculum_contents.id"))
    
    # Interaction metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Interaction type and data
    interaction_type = Column(String)  # "content_selection", "time_spent", "performance", etc.
    content_type = Column(String)  # "video", "text", "interactive", etc.
    
    # Metrics
    engagement_time_seconds = Column(Integer, default=0)
    engagement_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)
    preference_indicated = Column(Boolean, default=False)
    
    # Detailed interaction data
    interaction_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", backref="learning_interactions")
    content = relationship("CurriculumContent", backref="user_interactions")