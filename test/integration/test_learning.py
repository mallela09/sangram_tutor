Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/integration/test_learning.py
... import pytest
... from sqlalchemy.orm import Session
... 
... from sangram_tutor.models.user import User, UserRole
... from sangram_tutor.models.curriculum import CurriculumTopic, CurriculumContent
... from sangram_tutor.models.progress import Progress, CompletionStatus
... from sangram_tutor.ml.learning_path import LearningPathGenerator
... from sangram_tutor.utils.security import get_password_hash
... 
... def test_learning_path_flow(db: Session):
...     """Test a complete learning path flow."""
...     # 1. Create a test user
...     user = User(
...         username="student1",
...         email="student1@example.com",
...         hashed_password=get_password_hash("password"),
...         role=UserRole.STUDENT,
...         grade_level=3
...     )
...     db.add(user)
...     db.commit()
...     
...     # 2. Create some curriculum items
...     topic = CurriculumTopic(
...         name="Test Topic",
...         description="A topic for testing",
...         subject="mathematics",
...         grade_level=3
...     )
...     db.add(topic)
...     db.commit()
...     
...     # Add content items of increasing difficulty
...     content1 = CurriculumContent(
...         title="Beginner Content",
...         description="Beginner level content",
        content_data='{"type": "test"}',
        content_type="concept",
        difficulty_level="beginner",
        topic_id=topic.id
    )
    
    content2 = CurriculumContent(
        title="Easy Content",
        description="Easy level content",
        content_data='{"type": "test"}',
        content_type="exercise",
        difficulty_level="easy",
        topic_id=topic.id
    )
    
    db.add_all([content1, content2])
    db.commit()
    
    # 3. Initialize the learning path generator
    path_generator = LearningPathGenerator(db)
    
    # 4. Get first recommended content (should be beginner)
    next_content = path_generator.get_next_content(user.id)
    assert next_content is not None
    assert next_content["difficulty_level"] == "beginner"
    
    # 5. Mark content as completed with good score
    progress = Progress(
        user_id=user.id,
        content_id=next_content["id"],
        status=CompletionStatus.COMPLETED,
        score=90.0
    )
    db.add(progress)
    db.commit()
    
    # 6. Get next content (should recommend more difficult content)
    next_content = path_generator.get_next_content(user.id)
    assert next_content is not None
