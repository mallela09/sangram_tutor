from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Float, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from models.base import Base

# Enum for recommendation types
class RecommendationType(str, enum.Enum):
    CONTENT = "content"
    TOPIC = "topic"
    PATH = "path"
    ACTIVITY = "activity"
    REMEDIAL = "remedial"
    CHALLENGE = "challenge"

# Recommendation model
class Recommendation(Base):
    """Model for content and learning recommendations."""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # What is being recommended
    recommendation_type = Column(Enum(RecommendationType))
    content_id = Column(Integer, ForeignKey("curriculum_contents.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"), nullable=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)
    
    # Recommendation metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Recommendation properties
    title = Column(String)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    relevance_score = Column(Float, default=0.0)
    priority = Column(Integer, default=0)
    
    # User interaction
    viewed_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Algorithm information
    algorithm_name = Column(String, nullable=True)
    algorithm_version = Column(String, nullable=True)
    algorithm_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", backref="recommendations")
    content = relationship("CurriculumContent", backref="recommendations")
    topic = relationship("CurriculumTopic", backref="recommendations")
    path = relationship("LearningPath", backref="content_recommendations")

# Recommendation feedback model
class RecommendationFeedback(Base):
    """Model for tracking feedback on recommendations."""
    __tablename__ = "recommendation_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Feedback data
    created_at = Column(DateTime, default=datetime.utcnow)
    feedback_type = Column(String)  # "like", "dislike", "not_relevant", etc.
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comments = Column(Text, nullable=True)
    
    # Performance after recommendation
    subsequent_score = Column(Float, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    completed_successfully = Column(Boolean, nullable=True)
    
    # Relationships
    recommendation = relationship("Recommendation", backref="feedback")
    user = relationship("User", backref="recommendation_feedback")