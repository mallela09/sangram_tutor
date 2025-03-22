from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Float, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base

# Association table for learning path items
learning_path_items = Table(
    "learning_path_items",
    Base.metadata,
    Column("path_id", Integer, ForeignKey("learning_paths.id"), primary_key=True),
    Column("content_id", Integer, ForeignKey("curriculum_contents.id"), primary_key=True),
    Column("order", Integer)
)

# Learning path model
class LearningPath(Base):
    """Model for personalized learning paths."""
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text, nullable=True)
    
    # Path metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Path properties
    path_type = Column(String)  # "personalized", "standard", "remedial", etc.
    grade_level = Column(Integer, nullable=True)
    subject = Column(String, nullable=True)
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    last_accessed_at = Column(DateTime, nullable=True)
    estimated_time_minutes = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", backref="learning_paths")
    content_items = relationship(
        "CurriculumContent",
        secondary=learning_path_items,
        order_by=learning_path_items.c.order,
        backref="learning_paths"
    )

# Learning path recommendation model
class PathRecommendation(Base):
    """Model for learning path recommendations."""
    __tablename__ = "path_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    path_id = Column(Integer, ForeignKey("learning_paths.id"))
    
    # Recommendation metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Recommendation properties
    reason = Column(Text, nullable=True)
    relevance_score = Column(Float, default=0.0)
    priority = Column(Integer, default=0)
    
    # User interaction
    viewed_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="path_recommendations")
    path = relationship("LearningPath", backref="recommendations")