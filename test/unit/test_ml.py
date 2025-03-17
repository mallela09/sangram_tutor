Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/unit/test_ml.py
... import pytest
... from sqlalchemy.orm import Session
... 
... from sangram_tutor.ml.learning_style_detector import LearningStyleDetector
... from sangram_tutor.models.user import User, UserRole
... from sangram_tutor.utils.security import get_password_hash
... 
... def test_learning_style_detection_new_user(db: Session):
...     """Test learning style detection for a new user with no history."""
...     # Create test user
...     test_user = User(
...         username="newuser",
...         email="new@example.com",
...         hashed_password=get_password_hash("password"),
...         role=UserRole.STUDENT
...     )
...     db.add(test_user)
...     db.commit()
...     
...     # Initialize detector
...     detector = LearningStyleDetector(db)
...     
...     # Get style predictions
...     styles = detector.predict_learning_styles(test_user.id)
...     
...     # For a new user, should return balanced affinities
...     assert styles is not None
...     assert isinstance(styles, dict)
...     assert len(styles) > 0
...     
...     # All values should be around 0.5 for a new user
...     for style, value in styles.items():
