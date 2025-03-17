Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/conftest.py
... import os
... import pytest
... from sqlalchemy import create_engine
... from sqlalchemy.orm import sessionmaker
... 
... from sangram_tutor.models.base import Base
... from sangram_tutor.db.session import get_db
... 
... # Create a test database engine
... TEST_DATABASE_URL = "sqlite:///./test.db"
... test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
... TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
... 
... @pytest.fixture(scope="function")
... def db():
...     """Create a fresh database for each test."""
...     # Create tables
...     Base.metadata.create_all(bind=test_engine)
...     
...     # Create session
...     db = TestingSessionLocal()
...     try:
...         yield db
...     finally:
...         db.close()
...         # Clean up after test
...         Base.metadata.drop_all(bind=test_engine)
... 
... @pytest.fixture
... def client():
...     """Create a test client for the FastAPI app."""
...     from fastapi.testclient import TestClient
...     from sangram_tutor.main import app
...     
    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clear any overrides
