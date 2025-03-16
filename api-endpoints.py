# sangram_tutor/api/auth.py
from datetime import timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sangram_tutor.db.session import get_db
from sangram_tutor.models.user import User
from sangram_tutor.utils.security import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str


class UserCreate(BaseModel):
    """User creation request model."""
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = "student"
    grade_level: Optional[int] = None


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    This endpoint follows the OAuth2 password flow with form submission.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    This endpoint is simplified for the prototype. In a production system,
    it would include email verification, captcha, etc.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists (if provided)
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    from sangram_tutor.utils.security import get_password_hash
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        grade_level=user_data.grade_level,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}


# sangram_tutor/api/users.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sangram_tutor.db.session import get_db
from sangram_tutor.models.user import User, UserRole
from sangram_tutor.utils.auth import get_current_active_user
from sangram_tutor.utils.permissions import Permission, require_permission

router = APIRouter(prefix="/users", tags=["users"])


class UserProfile(BaseModel):
    """User profile response model."""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    grade_level: Optional[int] = None
    avatar: Optional[str] = None
    is_active: bool
    
    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    """User update request model."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    grade_level: Optional[int] = None
    avatar: Optional[str] = None


@router.get("/me", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get the profile of the currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update the profile of the currently authenticated user."""
    # Update user attributes
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.grade_level is not None:
        current_user.grade_level = user_data.grade_level
    if user_data.avatar is not None:
        current_user.avatar = user_data.avatar
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/", response_model=List[UserProfile])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    """
    List all users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        role: Filter by user role
    """
    query = db.query(User)
    
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
    
    users = query.offset(skip).limit(limit).all()
    return users


# sangram_tutor/api/learning.py
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sangram_tutor.db.session import get_db
from sangram_tutor.models.user import User
from sangram_tutor.models.curriculum import CurriculumContent, CurriculumTopic
from sangram_tutor.models.progress import Progress, CompletionStatus
from sangram_tutor.utils.auth import get_current_active_user
from sangram_tutor.ml.learning_path import LearningPathGenerator
from sangram_tutor.ml.recommendation import ContentRecommender
from sangram_tutor.ml.learning_style_detector import LearningStyleDetector

router = APIRouter(prefix="/learning", tags=["learning"])


class TopicResponse(BaseModel):
    """Topic response model."""
    id: int
    name: str
    description: Optional[str] = None
    subject: str
    grade_level: int
    standard_code: Optional[str] = None


class ContentResponse(BaseModel):
    """Content response model."""
    id: int
    title: str
    description: Optional[str] = None
    content_type: str
    difficulty_level: str
    estimated_time_minutes: int
    points_reward: int
    topic_id: int
    content_data: Dict


class ProgressUpdate(BaseModel):
    """Progress update request model."""
    status: str
    score: Optional[float] = None
    time_spent_seconds: Optional[int] = None
    engagement_score: Optional[float] = None
    mistakes_data: Optional[Dict] = None
    notes: Optional[str] = None


class ProgressResponse(BaseModel):
    """Progress response model."""
    content_id: int
    status: str
    score: Optional[float] = None
    attempts: int
    time_spent_seconds: Optional[int] = None
    last_interaction: Optional[str] = None
    completed_at: Optional[str] = None
    confidence_level: Optional[float] = None


@router.get("/topics", response_model=List[TopicResponse])
async def get_topics(
    grade_level: Optional[int] = None,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available curriculum topics.
    
    Args:
        grade_level: Optional filter by grade level
        subject: Optional filter by subject
    """
    query = db.query(CurriculumTopic)
    
    # Apply filters
    if grade_level is not None:
        query = query.filter(CurriculumTopic.grade_level == grade_level)
    
    if subject is not None:
        query = query.filter(CurriculumTopic.subject == subject)
    
    # Default to user's grade level if set
    if grade_level is None and current_user.grade_level is not None:
        query = query.filter(CurriculumTopic.grade_level == current_user.grade_level)
    
    topics = query.all()
    return topics


@router.get("/topics/{topic_id}/content", response_model=List[ContentResponse])
async def get_topic_content(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get content items for a specific topic.
    
    Args:
        topic_id: ID of the topic to get content for
    """
    # Check if topic exists
    topic = db.query(CurriculumTopic).filter_by(id=topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {topic_id} not found"
        )
    
    # Get all content for the topic
    content_items = db.query(CurriculumContent).filter_by(topic_id=topic_id).all()
    
    # Convert content_data JSON string to dict for each item
    import json
    for item in content_items:
        item.content_data = json.loads(item.content_data)
    
    return content_items


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific content item.
    
    Args:
        content_id: ID of the content to get
    """
    content = db.query(CurriculumContent).filter_by(id=content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )
    
    # Convert content_data JSON string to dict
    import json
    content.content_data = json.loads(content.content_data)
    
    return content


@router.post("/content/{content_id}/progress", response_model=ProgressResponse)
async def update_progress(
    content_id: int,
    progress_data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update progress for a content item.
    
    Args:
        content_id: ID of the content to update progress for
        progress_data: Progress update data
    """
    # Check if content exists
    content = db.query(CurriculumContent).filter_by(id=content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )
    
    # Get existing progress or create new
    progress = db.query(Progress).filter_by(
        user_id=current_user.id,
        content_id=content_id
    ).first()
    
    from datetime import datetime
    
    if progress:
        # Update existing progress
        try:
            status_enum = CompletionStatus(progress_data.status)
            progress.status = status_enum
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {progress_data.status}"
            )
        
        if progress_data.score is not None:
            progress.score = progress_data.score
        
        if progress_data.time_spent_seconds is not None:
            progress.time_spent_seconds = (progress.time_spent_seconds or 0) + progress_data.time_spent_seconds
        
        if progress_data.engagement_score is not None:
            progress.engagement_score = progress_data.engagement_score
        
        if progress_data.mistakes_data is not None:
            import json
            progress.mistakes_data = json.dumps(progress_data.mistakes_data)
        
        if progress_data.notes is not None:
            progress.notes = progress_data.notes
        
        # Increment attempts if appropriate
        if progress_data.status in ["completed", "mastered"]:
            progress.attempts += 1
        
        # Update timestamps
        progress.last_interaction = datetime.utcnow()
        
        if progress_data.status in ["completed", "mastered"] and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
    else:
        # Create new progress
        try:
            status_enum = CompletionStatus(progress_data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {progress_data.status}"
            )
        
        import json
        mistakes_json = json.dumps(progress_data.mistakes_data) if progress_data.mistakes_data else None
        
        # Set completion timestamp if applicable
        completed_at = None
        if progress_data.status in ["completed", "mastered"]:
            completed_at = datetime.utcnow()
        
        progress = Progress(
            user_id=current_user.id,
            content_id=content_id,
            status=status_enum,
            score=progress_data.score,
            attempts=1 if progress_data.status in ["completed", "mastered"] else 0,
            time_spent_seconds=progress_data.time_spent_seconds,
            last_interaction=datetime.utcnow(),
            completed_at=completed_at,
            engagement_score=progress_data.engagement_score,
            mistakes_data=mistakes_json,
            notes=progress_data.notes
        )
        db.add(progress)
    
    db.commit()
    db.refresh(progress)
    
    return {
        "content_id": progress.content_id,
        "status": progress.status.value,
        "score": progress.score,
        "attempts": progress.attempts,
        "time_spent_seconds": progress.time_spent_seconds,
        "last_interaction": progress.last_interaction.isoformat() if progress.last_interaction else None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        "confidence_level": progress.confidence_level
    }


@router.get("/next-content", response_model=ContentResponse)
async def get_next_content(
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the next recommended content for the user.
    
    Args:
        topic_id: Optional topic ID to filter content by
    """
    # Use learning path generator to get next content
    path_generator = LearningPathGenerator(db)
    next_content = path_generator.get_next_content(current_user.id, topic_id)
    
    if not next_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable content found"
        )
    
    return next_content


@router.get("/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get personalized content recommendations.
    
    Args:
        limit: Maximum number of recommendations to return
    """
    recommender = ContentRecommender(db)
    recommendations = recommender.get_personalized_recommendations(current_user.id, limit)
    
    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations available"
        )
    
    return recommendations


@router.get("/learning-styles", response_model=Dict[str, float])
async def get_learning_styles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get predicted learning style affinities for the current user."""
    detector = LearningStyleDetector(db)
    styles = detector.predict_learning_styles(current_user.id)
    
    return styles


# sangram_tutor/api/analytics.py
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sangram_tutor.db.session import get_db
from sangram_tutor.models.user import User
from sangram_tutor.utils.auth import get_current_active_user
from sangram_tutor.utils.permissions import Permission, require_permission
from sangram_tutor.ml.performance_analyzer import PerformanceAnalyzer

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/performance", response_model=Dict)
async def get_user_performance(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_ANALYTICS))
):
    """
    Get performance analytics for a user.
    
    Args:
        user_id: Optional user ID to get analytics for (defaults to current user)
    """
    # Default to current user if no user_id provided
    target_user_id = user_id or current_user.id
    
    # Check permission if requesting analytics for another user
    if target_user_id != current_user.id and not Permission.MANAGE_USERS in current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to view other user's analytics"
        )
    
    # Generate performance analytics
    analyzer = PerformanceAnalyzer(db)
    performance = analyzer.analyze_user_performance(target_user_id)
    
    return performance


# sangram_tutor/main.py
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from sangram_tutor.api import auth, users, learning, analytics
from sangram_tutor.db.session import get_db, engine
from sangram_tutor.db.init_db import init_db
from sangram_tutor.db.init_vectors import init_vector_db, update_content_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sangram Tutor API",
    description="API for the Sangram Tutor AI-powered math learning app",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application...")
    
    # Initialize database with tables and seed data
    db = next(get_db())
    try:
        init_db(db)
        
        # Initialize vector database
        init_vector_db()
        update_content_embeddings(db)
        
        logger.info("Application initialization complete")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Sangram Tutor API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
