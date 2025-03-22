from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Table, Boolean, Float
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.ext.associationproxy import association_proxy

from models.base import Base

# Association table for many-to-many prerequisite relationship
content_prerequisites = Table(
    "content_prerequisites",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("curriculum_contents.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("curriculum_contents.id"), primary_key=True)
)

# Enum classes
class Subject(str, enum.Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE = "language"
    OTHER = "other"

class ContentType(str, enum.Enum):
    CONCEPT = "concept"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    GAME = "game"
    VIDEO = "video"
    INTERACTIVE = "interactive"

class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADVANCED = "advanced"

# Curriculum topic model
class CurriculumTopic(Base):
    """Model for curriculum topics."""
    __tablename__ = "curriculum_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    subject = Column(Enum(Subject), index=True)
    grade_level = Column(Integer, index=True)
    standard_code = Column(String, nullable=True, index=True)
    
    # Relationship: one topic has many content items
    contents = relationship("CurriculumContent", back_populates="topic")
    
    # Additional metadata
    parent_topic_id = Column(Integer, ForeignKey("curriculum_topics.id"), nullable=True)
    sub_topics = relationship("CurriculumTopic", 
                             backref="parent_topic",
                             remote_side=[id])
    
    # For organization/sorting
    display_order = Column(Integer, nullable=True)

# Curriculum content model
class CurriculumContent(Base):
    """Model for curriculum content items."""
    __tablename__ = "curriculum_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    
    # Content type and data
    content_type = Column(Enum(ContentType), index=True)
    content_data = Column(Text)  # JSON stored as text
    
    # Difficulty and time estimation
    difficulty_level = Column(Enum(DifficultyLevel), index=True)
    estimated_time_minutes = Column(Integer)
    
    # Rewards and gamification
    points_reward = Column(Integer, default=0)
    has_certificate = Column(Boolean, default=False)
    
    # Foreign key relationship
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"))
    topic = relationship("CurriculumTopic", back_populates="contents")
    
    # Many-to-many prerequisite relationship
    prerequisites = relationship(
        "CurriculumContent",
        secondary=content_prerequisites,
        primaryjoin=id==content_prerequisites.c.content_id,
        secondaryjoin=id==content_prerequisites.c.prerequisite_id,
        backref="required_by"
    )
    
    # For organization/sorting
    display_order = Column(Integer, nullable=True)
    
    # Feedback and ratings
    average_rating = Column(Float, nullable=True)
    completion_count = Column(Integer, default=0)