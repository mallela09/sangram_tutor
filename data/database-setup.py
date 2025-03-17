# sangram_tutor/db/session.py
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment or use default SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sangram_tutor.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get DB session
def get_db() -> Generator:
    """
    Dependency function to get a database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# sangram_tutor/db/init_db.py
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from sangram_tutor.db.session import engine
from sangram_tutor.models.base import Base
from sangram_tutor.models.user import User, UserRole
from sangram_tutor.models.curriculum import (
    CurriculumTopic, CurriculumContent, 
    Subject, ContentType, DifficultyLevel
)
from sangram_tutor.utils.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """Initialize the database with tables and seed data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Created database tables")
    
    # Check if we need to seed the database
    user_count = db.query(User).count()
    if user_count > 0:
        logger.info(f"Database already contains {user_count} users. Skipping seed data.")
        return
    
    # Seed admin user
    admin_user = User(
        username="admin",
        email="admin@sangramtutor.com",
        hashed_password=get_password_hash("admin123"),  # Change this in production!
        role=UserRole.ADMIN,
        full_name="System Administrator",
        is_active=True,
    )
    db.add(admin_user)
    
    # Seed demo student
    demo_student = User(
        username="student",
        email="student@example.com",
        hashed_password=get_password_hash("student123"),
        role=UserRole.STUDENT,
        full_name="Demo Student",
        grade_level=3,
        birth_date=datetime(2017, 1, 1),  # 8 years old
        is_active=True,
    )
    db.add(demo_student)
    
    # Seed demo parent
    demo_parent = User(
        username="parent",
        email="parent@example.com",
        hashed_password=get_password_hash("parent123"),
        role=UserRole.PARENT,
        full_name="Demo Parent",
        is_active=True,
    )
    db.add(demo_parent)
    
    # Connect parent and child
    demo_student.parent_id = demo_parent.id
    
    # Add sample curriculum topics for Grade 1 Math (NCERT)
    topics = [
        CurriculumTopic(
            name="Shapes and Space",
            description="Concepts related to basic shapes, spatial understanding.",
            subject=Subject.MATHEMATICS,
            grade_level=1,
            standard_code="NCERT-MATH-G1-T1",
        ),
        CurriculumTopic(
            name="Numbers from 1 to 9",
            description="Counting, reading and writing numbers from 1 to 9.",
            subject=Subject.MATHEMATICS,
            grade_level=1,
            standard_code="NCERT-MATH-G1-T2",
        ),
        CurriculumTopic(
            name="Addition",
            description="Basic addition concepts with numbers up to 9.",
            subject=Subject.MATHEMATICS,
            grade_level=1,
            standard_code="NCERT-MATH-G1-T3",
        ),
    ]
    
    for topic in topics:
        db.add(topic)
    
    # Commit to get IDs
    db.commit()
    
    # Add sample content for each topic
    # Shapes topic content
    shapes_contents = [
        CurriculumContent(
            topic_id=topics[0].id,
            title="Introduction to Shapes",
            description="Learn about basic shapes like circle, square, triangle.",
            content_data='{"type": "concept", "elements": [{"type": "text", "content": "Shapes are all around us!"}, {"type": "image", "url": "circle.png"}, {"type": "image", "url": "square.png"}, {"type": "image", "url": "triangle.png"}]}',
            content_type=ContentType.CONCEPT,
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_time_minutes=5,
        ),
        CurriculumContent(
            topic_id=topics[0].id,
            title="Shape Recognition Game",
            description="Fun game to practice recognizing different shapes.",
            content_data='{"type": "game", "game_type": "matching", "items": [{"question": "circle.png", "answer": "Circle"}, {"question": "square.png", "answer": "Square"}, {"question": "triangle.png", "answer": "Triangle"}]}',
            content_type=ContentType.GAME,
            difficulty_level=DifficultyLevel.EASY,
            estimated_time_minutes=10,
            points_reward=15,
        ),
    ]
    
    # Numbers topic content
    numbers_contents = [
        CurriculumContent(
            topic_id=topics[1].id,
            title="Counting from 1 to 5",
            description="Learn to count objects from 1 to 5.",
            content_data='{"type": "concept", "elements": [{"type": "text", "content": "Let\'s count together!"}, {"type": "interactive", "counts": [1, 2, 3, 4, 5], "objects": ["apple", "ball", "cat", "dog", "elephant"]}]}',
            content_type=ContentType.CONCEPT,
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_time_minutes=8,
        ),
        CurriculumContent(
            topic_id=topics[1].id,
            title="Writing Numbers Quiz",
            description="Practice writing numbers from 1 to 5.",
            content_data='{"type": "quiz", "questions": [{"prompt": "Write the number:", "image": "one_finger.png", "answer": "1"}, {"prompt": "Write the number:", "image": "two_fingers.png", "answer": "2"}]}',
            content_type=ContentType.QUIZ,
            difficulty_level=DifficultyLevel.EASY,
            estimated_time_minutes=12,
            points_reward=20,
        ),
    ]
    
    # Addition topic content
    addition_contents = [
        CurriculumContent(
            topic_id=topics[2].id,
            title="Adding with Pictures",
            description="Learn addition using visual representations.",
            content_data='{"type": "concept", "elements": [{"type": "text", "content": "Addition means combining things together!"}, {"type": "interactive", "left": 2, "right": 3, "result": 5}]}',
            content_type=ContentType.CONCEPT,
            difficulty_level=DifficultyLevel.EASY,
            estimated_time_minutes=10,
        ),
        CurriculumContent(
            topic_id=topics[2].id,
            title="Addition Practice",
            description="Solve simple addition problems.",
            content_data='{"type": "exercise", "problems": [{"prompt": "1 + 2 = ?", "answer": 3}, {"prompt": "3 + 1 = ?", "answer": 4}, {"prompt": "2 + 2 = ?", "answer": 4}]}',
            content_type=ContentType.EXERCISE,
            difficulty_level=DifficultyLevel.MEDIUM,
            estimated_time_minutes=15,
            points_reward=25,
        ),
    ]
    
    # Add all content
    for content in shapes_contents + numbers_contents + addition_contents:
        db.add(content)
    
    # Set prerequisites
    # Addition practice requires introduction to addition
    addition_contents[1].prerequisites.append(addition_contents[0])
    
    # Commit all changes
    db.commit()
    
    logger.info("Database seeded with initial data")


# sangram_tutor/db/init_vectors.py
import json
import logging
import numpy as np
import faiss
import os
from pathlib import Path

from sqlalchemy.orm import Session

from sangram_tutor.models.curriculum import CurriculumContent

logger = logging.getLogger(__name__)

# Directory to store vector indices
VECTOR_DIR = Path("./vector_indices")
VECTOR_DIR.mkdir(exist_ok=True)

def init_vector_db() -> None:
    """Initialize the vector database for content embeddings."""
    # Check if index already exists
    index_path = VECTOR_DIR / "content_embeddings.index"
    
    if index_path.exists():
        logger.info("Vector index already exists. Skipping initialization.")
        return
    
    # Create a simple vector index
    # For the prototype, we'll use random vectors - in production this would use 
    # actual embeddings from a model like sentence-transformers
    dimension = 128  # embedding dimension
    index = faiss.IndexFlatL2(dimension)
    
    logger.info(f"Created new vector index with dimension {dimension}")
    
    # Save the empty index
    faiss.write_index(index, str(index_path))
    logger.info(f"Saved empty vector index to {index_path}")


def update_content_embeddings(db: Session) -> None:
    """
    Update vector embeddings for all curriculum content.
    In a real implementation, this would use a language model to create embeddings.
    For the prototype, we'll use random vectors.
    """
    index_path = VECTOR_DIR / "content_embeddings.index"
    if not os.path.exists(index_path):
        init_vector_db()
    
    # Load the index
    index = faiss.read_index(str(index_path))
    
    # Get all content items
    contents = db.query(CurriculumContent).all()
    
    if not contents:
        logger.warning("No content found in database to embed")
        return
    
    # Generate "embeddings" (random vectors for prototype)
    # In production, these would be actual embeddings from content text
    embeddings = []
    content_ids = []
    
    for content in contents:
        # Parse content data to extract text
        try:
            content_data = json.loads(content.content_data)
            # In a real implementation, we would extract text from content_data
            # and use a model to generate an embedding

            # For prototype, generate a random vector
            embedding = np.random.random(128).astype('float32')
            embeddings.append(embedding)
            content_ids.append(content.id)
        except Exception as e:
            logger.error(f"Error processing content {content.id}: {e}")
    
    if not embeddings:
        logger.warning("No embeddings generated")
        return
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')
    
    # Add to index
    index.add(embeddings_array)
    
    # Save index
    faiss.write_index(index, str(index_path))
    
    # Save mapping of indices to content IDs
    id_mapping = {idx: content_id for idx, content_id in enumerate(content_ids)}
    with open(VECTOR_DIR / "content_id_mapping.json", "w") as f:
        json.dump(id_mapping, f)
    
    logger.info(f"Updated vector index with {len(embeddings)} content embeddings")
