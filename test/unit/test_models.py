Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/unit/test_models.py
... import pytest
... from sqlalchemy.orm import Session
... 
... from sangram_tutor.models.user import User, UserRole
... from sangram_tutor.utils.security import get_password_hash
... 
... def test_create_user(db: Session):
...     """Test creating and retrieving a user."""
...     # Create test user
...     test_user = User(
...         username="testuser",
...         email="test@example.com",
...         hashed_password=get_password_hash("testpassword"),
...         role=UserRole.STUDENT,
...         full_name="Test User",
...         grade_level=3
...     )
...     
...     # Add to the database
...     db.add(test_user)
...     db.commit()
...     db.refresh(test_user)
...     
...     # Retrieve from database
...     retrieved_user = db.query(User).filter_by(username="testuser").first()
...     
...     # Assertions
...     assert retrieved_user is not None
...     assert retrieved_user.username == "testuser"
...     assert retrieved_user.email == "test@example.com"
...     assert retrieved_user.role == UserRole.STUDENT
