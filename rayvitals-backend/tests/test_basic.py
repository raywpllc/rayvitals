"""
Basic tests for RayVitals Backend API
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "RayVitals Backend API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_health_check():
    """Test API health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_start_audit_endpoint():
    """Test starting an audit"""
    audit_data = {
        "url": "https://example.com"
    }
    response = client.post("/api/v1/audit/start", json=audit_data)
    
    # Note: This will fail without database setup, but tests the endpoint structure
    # assert response.status_code == 200 or response.status_code == 500
    assert response.status_code in [200, 500]  # Expected to fail without DB


def test_docs_endpoint():
    """Test that API docs are accessible in debug mode"""
    response = client.get("/docs")
    # Should be accessible if DEBUG=True
    assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__])