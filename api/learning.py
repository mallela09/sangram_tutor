from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from api.auth import get_current_active_user, User

router = APIRouter(tags=["learning"], prefix="/learning")

# Enum classes
class ContentType(str, Enum):
    CONCEPT = "concept"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    GAME = "game"
    VIDEO = "video"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADVANCED = "advanced"

class Subject(str, Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE = "language"

# Pydantic models
class TopicBase(BaseModel):
    name: str
    description: str
    subject: Subject
    grade_level: int
    standard_code: Optional[str] = None

class Topic(TopicBase):
    id: int

class ContentBase(BaseModel):
    title: str
    description: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    estimated_time_minutes: int
    content_data: Dict[str, Any]
    points_reward: Optional[int] = 0

class Content(ContentBase):
    id: int
    topic_id: int

class ProgressUpdate(BaseModel):
    content_id: int
    completed: bool
    score: Optional[int] = None
    time_spent_seconds: Optional[int] = None
    answers: Optional[Dict[str, Any]] = None

class UserProgress(BaseModel):
    user_id: str
    content_id: int
    completed: bool
    score: Optional[int] = None
    completed_at: Optional[str] = None
    attempts: int = 0

# Mock database
topics_db = {
    1: {
        "id": 1,
        "name": "Shapes and Space",
        "description": "Concepts related to basic shapes, spatial understanding.",
        "subject": Subject.MATHEMATICS,
        "grade_level": 1,
        "standard_code": "NCERT-MATH-G1-T1",
    },
    2: {
        "id": 2,
        "name": "Numbers from 1 to 9",
        "description": "Counting, reading and writing numbers from 1 to 9.",
        "subject": Subject.MATHEMATICS,
        "grade_level": 1,
        "standard_code": "NCERT-MATH-G1-T2",
    }
}

contents_db = {
    1: {
        "id": 1,
        "topic_id": 1,
        "title": "Introduction to Shapes",
        "description": "Learn about basic shapes like circle, square, triangle.",
        "content_type": ContentType.CONCEPT,
        "difficulty_level": DifficultyLevel.BEGINNER,
        "estimated_time_minutes": 5,
        "points_reward": 10,
        "content_data": {
            "type": "concept", 
            "elements": [
                {"type": "text", "content": "Shapes are all around us!"},
                {"type": "image", "url": "circle.png"},
                {"type": "image", "url": "square.png"},
                {"type": "image", "url": "triangle.png"}
            ]
        }
    },
    2: {
        "id": 2,
        "topic_id": 1,
        "title": "Shape Recognition Game",
        "description": "Fun game to practice recognizing different shapes.",
        "content_type": ContentType.GAME,
        "difficulty_level": DifficultyLevel.EASY,
        "estimated_time_minutes": 10,
        "points_reward": 15,
        "content_data": {
            "type": "game", 
            "game_type": "matching", 
            "items": [
                {"question": "circle.png", "answer": "Circle"},
                {"question": "square.png", "answer": "Square"},
                {"question": "triangle.png", "answer": "Triangle"}
            ]
        }
    }
}

progress_db = {}  # user_id-content_id -> progress

# API Endpoints
@router.get("/topics", response_model=List[Topic])
async def get_topics(
    grade_level: Optional[int] = None,
    subject: Optional[Subject] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get all topics, optionally filtered by grade level and subject."""
    filtered_topics = list(topics_db.values())
    
    if grade_level is not None:
        filtered_topics = [t for t in filtered_topics if t["grade_level"] == grade_level]
    
    if subject is not None:
        filtered_topics = [t for t in filtered_topics if t["subject"] == subject]
    
    return filtered_topics

@router.get("/topics/{topic_id}", response_model=Topic)
async def get_topic(topic_id: int, current_user: User = Depends(get_current_active_user)):
    """Get a specific topic by ID."""
    if topic_id not in topics_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {topic_id} not found"
        )
    return topics_db[topic_id]

@router.get("/topics/{topic_id}/contents", response_model=List[Content])
async def get_topic_contents(
    topic_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    """Get all content items for a specific topic."""
    if topic_id not in topics_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {topic_id} not found"
        )
    
    topic_contents = [c for c in contents_db.values() if c["topic_id"] == topic_id]
    return topic_contents

@router.get("/contents/{content_id}", response_model=Content)
async def get_content(content_id: int, current_user: User = Depends(get_current_active_user)):
    """Get a specific content item by ID."""
    if content_id not in contents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )
    return contents_db[content_id]

@router.post("/progress", status_code=status.HTTP_201_CREATED)
async def update_progress(
    progress: ProgressUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a user's progress on a content item."""
    if progress.content_id not in contents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {progress.content_id} not found"
        )
    
    progress_key = f"{current_user.username}-{progress.content_id}"
    
    # Get existing progress or create new
    existing = progress_db.get(progress_key, {
        "user_id": current_user.username,
        "content_id": progress.content_id,
        "completed": False,
        "score": None,
        "completed_at": None,
        "attempts": 0
    })
    
    # Update progress
    existing["attempts"] += 1
    
    if progress.completed:
        import datetime
        existing["completed"] = True
        existing["completed_at"] = datetime.datetime.now().isoformat()
        
    if progress.score is not None:
        existing["score"] = progress.score
        
    # Save updated progress
    progress_db[progress_key] = existing
    
    return {"status": "success", "message": "Progress updated"}

@router.get("/progress", response_model=List[UserProgress])
async def get_user_progress(current_user: User = Depends(get_current_active_user)):
    """Get all progress for the current user."""
    user_progress = []
    
    for key, progress in progress_db.items():
        if key.startswith(f"{current_user.username}-"):
            user_progress.append(progress)
            
    return user_progress

@router.get("/progress/{content_id}", response_model=UserProgress)
async def get_content_progress(
    content_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get a user's progress for a specific content item."""
    progress_key = f"{current_user.username}-{content_id}"
    
    if progress_key not in progress_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress found for content ID {content_id}"
        )
        
    return progress_db[progress_key]
