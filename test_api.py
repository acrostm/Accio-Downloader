import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Accio-Downloader"}

def test_parse_video():
    # Test with a known youtube URL (Me at the zoo)
    response = client.post(
        "/api/v1/video/parse",
        json={"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "formats" in data
    assert isinstance(data["formats"], list)
