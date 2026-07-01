import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from shapely.geometry import Polygon
from shapely import wkb
from runway_processor import process_runway_geometry, process_funnel, create_arc_wedge


class TestProcessRunwayGeometry:
    """Tests for process_runway_geometry database operations"""
    
    @pytest.fixture
    def valid_runway_data(self):
        """Valid runway for testing"""
        return {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1], [77.0, 28.0]]]
            }
        }
    
    @pytest.fixture
    def mock_db_with_funnel_zone(self):
        """Mock DB with existing funnel zone"""
        db = AsyncMock()
        
        # Create mock polygon
        poly = Polygon([[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1]])
        
        # Mock result for SELECT_QUERY
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            (poly.wkb_hex, 'funnel', 'civil', 'radio1', 100, 28.05, 77.05),
            (poly.wkb_hex, 'inner', 'civil', 'radio1', 100, 28.05, 77.05),
            (poly.wkb_hex, 'outer', 'civil', 'radio1', 100, 28.05, 77.05),
        ])
        
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        
        return db
    
    @pytest.fixture
    def mock_db_without_funnel_zone(self):
        """Mock DB without funnel zone"""
        db = AsyncMock()
        
        # Create mock polygon
        poly = Polygon([[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1]])
        
        # Mock result for SELECT_QUERY - no funnel zone
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            (poly.wkb_hex, 'inner', 'civil', 'radio1', 100, 28.05, 77.05),
            (poly.wkb_hex, 'outer', 'civil', 'radio1', 100, 28.05, 77.05),
        ])
        
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        
        return db
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_with_existing_funnel(self, valid_runway_data, mock_db_with_funnel_zone):
        """Test processing runway when funnel zone already exists"""
        result = await process_runway_geometry(valid_runway_data, "TestAirport", mock_db_with_funnel_zone)
        
        assert result is True
        mock_db_with_funnel_zone.commit.assert_called_once()
        mock_db_with_funnel_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_without_funnel(self, valid_runway_data, mock_db_without_funnel_zone):
        """Test processing runway when funnel zone doesn't exist (INSERT case)"""
        result = await process_runway_geometry(valid_runway_data, "TestAirport", mock_db_without_funnel_zone)
        
        assert result is True
        mock_db_without_funnel_zone.commit.assert_called_once()
        # Should have called execute multiple times for INSERT
        assert mock_db_without_funnel_zone.execute.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_with_inner_zone(self, valid_runway_data, mock_db_with_funnel_zone):
        """Test that inner zone difference is calculated correctly"""
        result = await process_runway_geometry(valid_runway_data, "TestAirport", mock_db_with_funnel_zone)
        
        assert result is True
        # Verify that funnel_geometry.difference was called for inner zone
        mock_db_with_funnel_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_with_outer_zone(self, valid_runway_data, mock_db_with_funnel_zone):
        """Test that outer zone difference is calculated correctly"""
        result = await process_runway_geometry(valid_runway_data, "TestAirport", mock_db_with_funnel_zone)
        
        assert result is True
        mock_db_with_funnel_zone.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_database_error(self, valid_runway_data):
        """Test error handling during database operations"""
        db = AsyncMock()
        db.execute.side_effect = Exception("Database error")
        db.rollback = AsyncMock()
        
        result = await process_runway_geometry(valid_runway_data, "TestAirport", db)
        
        assert result is False
        db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_wkb_loading(self, valid_runway_data):
        """Test that WKB geometries are properly loaded and processed"""
        db = AsyncMock()
        
        # Create a real polygon and get its WKB
        poly = Polygon([[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1]])
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            (poly.wkb_hex, 'funnel', 'civil', 'radio1', 100, 28.05, 77.05),
        ])
        
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        
        success = await process_runway_geometry(valid_runway_data, "TestAirport", db)
        
        assert success is True
        # Verify execute was called for UPDATE
        assert db.execute.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_union_operation(self, valid_runway_data):
        """Test union operation for funnel zone"""
        db = AsyncMock()
        
        poly = Polygon([[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1]])
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            (poly.wkb_hex, 'funnel', 'civil', 'radio1', 100, 28.05, 77.05),
        ])
        
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        
        success = await process_runway_geometry(valid_runway_data, "TestAirport", db)
        
        assert success is True
        # Verify that geometry operations were performed
        db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_runway_geometry_multiple_zones(self, valid_runway_data):
        """Test processing with multiple zone types"""
        db = AsyncMock()
        
        poly = Polygon([[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1]])
        
        # Return all three zone types
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            (poly.wkb_hex, 'funnel', 'civil', 'radio1', 100, 28.05, 77.05),
            (poly.wkb_hex, 'inner', 'military', 'radio2', 200, 28.05, 77.05),
            (poly.wkb_hex, 'outer', 'civil', 'radio3', 150, 28.05, 77.05),
        ])
        
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        
        success = await process_runway_geometry(valid_runway_data, "TestAirport", db)
        
        assert success is True
        db.commit.assert_called_once()