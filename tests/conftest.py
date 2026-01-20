import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from connect_db import get_db


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def mock_db_session():
    """Mock async database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def override_get_db(mock_db_session):
    """Override dependency injection for database"""
    async def _override():
        yield mock_db_session
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_tile_result():
    """Mock tile query result"""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (b'\x1f\x8b\x08\x00test_tile_data',) 
    return mock_result


@pytest.fixture
def mock_empty_tile_result():
    """Mock empty tile result"""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    return mock_result


@pytest.fixture
def mock_report_result():
    """Mock report query result"""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("funnel", "TestAirport", "civil", "120.5", 500, 5000.0),
        ("inner", "TestAirport", "civil", "120.5", 500, 3000.0),
    ]
    return mock_result


@pytest.fixture
def mock_no_results():
    """Mock empty query result"""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = None
    return mock_result


@pytest.fixture
def valid_runway_data():
    """Valid runway funnel data"""
    return {
        "airportName": "TestAirport",
        "features": [{
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1], [77.0, 28.0]]]
            }
        }]
    }
    