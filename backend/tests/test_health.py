from unittest.mock import MagicMock


def test_health_check_healthy(client, monkeypatch):
    """
    Test GET /health when database and redis are healthy.
    """
    # Mock Redis to return healthy ping
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: mock_redis)

    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"
    assert "timestamp" in data


def test_health_check_database_unhealthy(client, monkeypatch):
    """
    Test GET /health when database is unhealthy.
    """
    # Mock database session execute to raise exception
    def mock_execute(*args, **kwargs):
        raise Exception("DB Connection Lost")
    
    # We override db session execution in dependency_overrides
    from app.database import get_db
    from app.main import app
    
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DB Connection Lost")
    
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock Redis to return healthy ping
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: mock_redis)

    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "unhealthy"
    assert "unhealthy" in data["database"]
    assert data["redis"] == "healthy"
    
    app.dependency_overrides.clear()
