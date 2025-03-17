Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> # sangram_tutor/tests/unit/test_api.py
... from fastapi.testclient import TestClient
... 
... def test_health_endpoint(client):
...     """Test the health check endpoint."""
...     response = client.get("/health")
...     assert response.status_code == 200
...     assert "healthy" in response.json()["status"]
... 
... def test_root_endpoint(client):
...     """Test the root endpoint."""
...     response = client.get("/")
...     assert response.status_code == 200
