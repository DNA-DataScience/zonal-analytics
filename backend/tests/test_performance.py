import pytest
import time
from unittest.mock import patch, AsyncMock
from runway_processor import process_funnel


class TestPerformance:
    """Performance and response time tests"""
    
    def test_tile_endpoint_response_time(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test tile endpoint responds within acceptable time"""
        mock_db_session.execute.return_value = mock_tile_result
        
        start = time.time()
        response = client.get("/tiles/10/512/256.mvt")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0
    
    def test_empty_tile_response_time(self, client, override_get_db, mock_db_session, mock_empty_tile_result):
        """Test empty tile response time"""
        mock_db_session.execute.return_value = mock_empty_tile_result
        
        start = time.time()
        response = client.get("/tiles/10/512/256.mvt")
        elapsed = time.time() - start
        
        assert elapsed < 1.0
    
    def test_multiple_sequential_tile_requests(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test multiple sequential tile requests"""
        mock_db_session.execute.return_value = mock_tile_result
        
        start = time.time()
        for i in range(10):
            response = client.get(f"/tiles/{i % 10}/{512 + i}/{256 + i}.mvt")
            assert response.status_code == 200
        elapsed = time.time() - start
        
        avg_time = elapsed / 10
        assert avg_time < 1.0
    
    def test_funnel_generation_performance(self):
        """Test funnel generation performance"""
        runway = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.05, 28.0], [77.05, 28.05], [77.0, 28.05], [77.0, 28.0]]]
            }
        }
        
        start = time.time()
        for _ in range(100):
            funnel = process_funnel(runway)
            assert funnel.is_valid
        elapsed = time.time() - start
        
        avg_time = elapsed / 100
        assert avg_time < 0.1
    
    def test_report_endpoint_response_time(self, client, override_get_db, mock_db_session, mock_report_result):
        """Test report endpoint response time"""
        mock_db_session.execute.return_value = mock_report_result
        
        start = time.time()
        response = client.get("/report-generator?lat=28.5&lng=77.1&elev=100")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0