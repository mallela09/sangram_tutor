from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from api.auth import get_current_active_user, User

router = APIRouter(tags=["analytics"], prefix="/analytics")

# Enum classes
class TimeFrame(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"

class MetricType(str, Enum):
    COMPLETION_RATE = "completion_rate"
    TIME_SPENT = "time_spent"
    SCORE = "score"
    ATTEMPTS = "attempts"

# Pydantic models
class UserMetric(BaseModel):
    user_id: str
    metric_name: str
    value: float
    timestamp: datetime

class UserSummary(BaseModel):
    username: str
    topics_started: int
    topics_completed: int
    average_score: float
    total_time_spent_minutes: int
    points_earned: int

class TopicMetrics(BaseModel):
    topic_id: int
    topic_name: str
    completion_rate: float
    average_score: float
    average_time_minutes: float
    student_count: int

class ContentMetrics(BaseModel):
    content_id: int
    title: str
    completion_rate: float
    average_score: Optional[float] = None
    average_time_minutes: float
    difficulty_rating: float

# Sample analytics data
user_metrics_db = [
    {
        "user_id": "testuser",
        "metric_name": "topics_completed",
        "value": 3,
        "timestamp": datetime.now() - timedelta(days=1)
    },
    {
        "user_id": "testuser",
        "metric_name": "average_score",
        "value": 85.5,
        "timestamp": datetime.now() - timedelta(days=1)
    },
    {
        "user_id": "alice",
        "metric_name": "topics_completed",
        "value": 5,
        "timestamp": datetime.now() - timedelta(days=2)
    },
]

# Sample user summaries
user_summaries = {
    "testuser": {
        "username": "testuser",
        "topics_started": 5,
        "topics_completed": 3,
        "average_score": 85.5,
        "total_time_spent_minutes": 120,
        "points_earned": 450
    },
    "alice": {
        "username": "alice",
        "topics_started": 8,
        "topics_completed": 5,
        "average_score": 92.0,
        "total_time_spent_minutes": 180,
        "points_earned": 620
    }
}

# Sample topic metrics
topic_metrics = {
    1: {
        "topic_id": 1,
        "topic_name": "Shapes and Space",
        "completion_rate": 0.78,
        "average_score": 88.5,
        "average_time_minutes": 12.3,
        "student_count": 25
    },
    2: {
        "topic_id": 2,
        "topic_name": "Numbers from 1 to 9",
        "completion_rate": 0.85,
        "average_score": 90.2,
        "average_time_minutes": 15.7,
        "student_count": 22
    }
}

# Sample content metrics
content_metrics = {
    1: {
        "content_id": 1,
        "title": "Introduction to Shapes",
        "completion_rate": 0.95,
        "average_score": 92.0,
        "average_time_minutes": 6.2,
        "difficulty_rating": 1.2
    },
    2: {
        "content_id": 2,
        "title": "Shape Recognition Game",
        "completion_rate": 0.82,
        "average_score": 85.5,
        "average_time_minutes": 8.7,
        "difficulty_rating": 2.1
    }
}

# API Endpoints
@router.get("/user/summary", response_model=UserSummary)
async def get_user_summary(current_user: User = Depends(get_current_active_user)):
    """Get learning summary for the current user."""
    if current_user.username not in user_summaries:
        # Return empty summary if user not found
        return UserSummary(
            username=current_user.username,
            topics_started=0,
            topics_completed=0,
            average_score=0.0,
            total_time_spent_minutes=0,
            points_earned=0
        )
    
    return user_summaries[current_user.username]

@router.get("/user/metrics", response_model=List[Dict[str, Any]])
async def get_user_metrics(
    timeframe: TimeFrame = TimeFrame.WEEK,
    metric: Optional[MetricType] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get metrics for the current user over a timeframe."""
    # Filter metrics by user
    user_metrics = [m for m in user_metrics_db if m["user_id"] == current_user.username]
    
    # Apply timeframe filter
    cutoff_date = datetime.now()
    if timeframe == TimeFrame.DAY:
        cutoff_date = cutoff_date - timedelta(days=1)
    elif timeframe == TimeFrame.WEEK:
        cutoff_date = cutoff_date - timedelta(weeks=1)
    elif timeframe == TimeFrame.MONTH:
        cutoff_date = cutoff_date - timedelta(days=30)
    elif timeframe == TimeFrame.YEAR:
        cutoff_date = cutoff_date - timedelta(days=365)
    
    if timeframe != TimeFrame.ALL:
        user_metrics = [m for m in user_metrics if m["timestamp"] >= cutoff_date]
    
    # Apply metric filter if provided
    if metric:
        user_metrics = [m for m in user_metrics if m["metric_name"] == metric.value]
    
    # Convert to serializable format
    result = []
    for metric in user_metrics:
        result.append({
            "user_id": metric["user_id"],
            "metric_name": metric["metric_name"],
            "value": metric["value"],
            "timestamp": metric["timestamp"].isoformat()
        })
    
    return result

@router.get("/topics", response_model=List[TopicMetrics])
async def get_topic_metrics(
    grade_level: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get performance metrics for all topics."""
    metrics = list(topic_metrics.values())
    
    # Could filter by grade level in a real implementation
    
    return metrics

@router.get("/topics/{topic_id}", response_model=TopicMetrics)
async def get_topic_metric(
    topic_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get performance metrics for a specific topic."""
    if topic_id not in topic_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for topic ID {topic_id} not found"
        )
    
    return topic_metrics[topic_id]

@router.get("/contents/{content_id}", response_model=ContentMetrics)
async def get_content_metric(
    content_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get performance metrics for a specific content item."""
    if content_id not in content_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for content ID {content_id} not found"
        )
    
    return content_metrics[content_id]

@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    timeframe: TimeFrame = TimeFrame.WEEK,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get points leaderboard for students."""
    # Sample leaderboard data
    leaderboard = [
        {"username": "alice", "points": 620, "rank": 1},
        {"username": "bob", "points": 580, "rank": 2},
        {"username": "testuser", "points": 450, "rank": 3},
        {"username": "charlie", "points": 420, "rank": 4},
        {"username": "david", "points": 380, "rank": 5},
    ]
    
    # Limit results
    leaderboard = leaderboard[:limit]
    
    return leaderboard
