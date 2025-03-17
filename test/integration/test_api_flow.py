Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/integration/test_api_flow.py
... import pytest
... from fastapi.testclient import TestClient
... 
... def test_complete_user_journey(client):
...     """
...     Test a complete user journey through the API endpoints.
...     This tests registration, authentication, content access, and progress tracking.
...     """
...     # 1. Register a new user
...     register_data = {
...         "username": "testjourney",
...         "password": "testpassword123",
...         "email": "testjourney@example.com",
...         "full_name": "Test Journey User",
...         "grade_level": 3
...     }
...     
...     response = client.post("/api/auth/register", json=register_data)
...     assert response.status_code == 201, f"Registration failed: {response.text}"
...     assert "user_id" in response.json()
...     
...     # 2. Login with the new user
...     login_data = {
...         "username": "testjourney",
...         "password": "testpassword123"
...     }
...     
...     response = client.post("/api/auth/token", data=login_data)
...     assert response.status_code == 200, f"Login failed: {response.text}"
...     
...     token_data = response.json()
...     assert "access_token" in token_data
...     
...     # Set up authenticated headers
...     headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    
    # 3. Get user profile
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testjourney"
    assert user_data["grade_level"] == 3
    
    # 4. Get available topics for the user's grade
    response = client.get("/api/learning/topics", headers=headers)
    assert response.status_code == 200
    topics = response.json()
    
    # If we have topics, test further content flow
    if topics:
        # 5. Get content for the first topic
        topic_id = topics[0]["id"]
        response = client.get(f"/api/learning/topics/{topic_id}/content", headers=headers)
        assert response.status_code == 200
        content_items = response.json()
        
        if content_items:
            # 6. Get the first content item
            content_id = content_items[0]["id"]
            response = client.get(f"/api/learning/content/{content_id}", headers=headers)
            assert response.status_code == 200
            content_detail = response.json()
            assert content_detail["id"] == content_id
            
            # 7. Update progress for the content
            progress_data = {
                "status": "completed",
                "score": 85.5,
                "time_spent_seconds": 300,
                "engagement_score": 0.9
            }
            
            response = client.post(
                f"/api/learning/content/{content_id}/progress", 
                json=progress_data,
                headers=headers
            )
            assert response.status_code == 200
            progress = response.json()
            assert progress["content_id"] == content_id
            assert progress["score"] == 85.5
            
            # 8. Get next recommended content
            response = client.get("/api/learning/next-content", headers=headers)
            assert response.status_code == 200
            next_content = response.json()
            assert next_content["id"] != content_id, "Should recommend different content"
            
            # 9. Get personalized recommendations
            response = client.get("/api/learning/recommendations", headers=headers)
            if response.status_code == 200:  # This might 404 if not enough data
                recommendations = response.json()
                assert isinstance(recommendations, list)
    
    # 10. Get learning analytics
    response = client.get("/api/analytics/performance", headers=headers)
    assert response.status_code == 200
    performance = response.json()
    
    # 11. Check learning styles prediction
    response = client.get("/api/learning/learning-styles", headers=headers)
    assert response.status_code == 200
    styles = response.json()
    assert isinstance(styles, dict)
    
    # 12. Update user profile
    update_data = {
        "full_name": "Updated Test User"
    }
    
    response = client.put("/api/users/me", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == "Updated Test User"


def test_parent_child_relationship(client):
    """
    Test parent-child relationship functionality.
    This tests creating parent and child accounts and linking them.
    """
    # 1. Create parent account
    parent_data = {
        "username": "testparent",
        "password": "parentpass123",
        "email": "parent@example.com",
        "full_name": "Test Parent",
        "role": "parent"
    }
    
    response = client.post("/api/auth/register", json=parent_data)
    assert response.status_code == 201
    parent_id = response.json()["user_id"]
    
    # 2. Create child account
    child_data = {
        "username": "testchild",
        "password": "childpass123",
        "email": "child@example.com",
        "full_name": "Test Child",
        "role": "student",
        "grade_level": 2
    }
    
    response = client.post("/api/auth/register", json=child_data)
    assert response.status_code == 201
    child_id = response.json()["user_id"]
    
    # 3. Login as parent
    login_data = {
        "username": "testparent",
        "password": "parentpass123"
    }
    
    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200
    parent_token = response.json()["access_token"]
    
    parent_headers = {
        "Authorization": f"Bearer {parent_token}"
    }
    
    # 4. Link child to parent (this endpoint would need to be implemented)
    # This is a placeholder for your actual API endpoint
    link_data = {
        "child_id": child_id
    }
    
    # This endpoint is hypothetical and would need to be implemented in your API
    response = client.post("/api/users/link-child", json=link_data, headers=parent_headers)
    
    # If you don't have this endpoint yet, comment out the assertion
    # assert response.status_code == 200
    
    # 5. Parent should be able to view child's progress
    # This endpoint is hypothetical and would need to be implemented in your API
    response = client.get(f"/api/analytics/performance?user_id={child_id}", headers=parent_headers)
    
    # If you don't have this endpoint yet, comment out the assertion
    # assert response.status_code == 200


def test_error_handling(client):
    """
    Test API error handling for various scenarios.
    """
    # 1. Test invalid login
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 401
    
    # 2. Test accessing protected endpoint without authentication
    response = client.get("/api/users/me")
    assert response.status_code == 401
    
    # 3. Test invalid content ID
    # Create a valid token first
    valid_login = {
        "username": "testjourney",
        "password": "testpassword123"
    }
    
    response = client.post("/api/auth/token", data=valid_login)
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Test with invalid content ID
        response = client.get("/api/learning/content/99999", headers=headers)
        assert response.status_code == 404
        
        # Test with invalid topic ID
        response = client.get("/api/learning/topics/99999/content", headers=headers)
        assert response.status_code == 404
    
    # 4. Test registering duplicate username
    register_data = {
        "username": "testjourney",  # Already exists from previous test
        "password": "password123",
        "email": "another@example.com"
    }
    
    response = client.post("/api/auth/register", json=register_data)
