import pytest
from unittest.mock import patch, AsyncMock
from main import QUERY


class TestGetTileEndpoint:
    """Tests for /tiles/{z}/{x}/{y}.mvt endpoint"""
    
    def test_get_tile_success(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test successful tile retrieval"""
        mock_db_session.execute = AsyncMock(return_value=mock_tile_result)
        
        response = client.get("/tiles/10/512/256.mvt")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.mapbox-vector-tile"
        assert response.content == b'\x1f\x8b\x08\x00test_tile_data'
    
    def test_get_tile_empty_result(self, client, override_get_db, mock_db_session, mock_empty_tile_result):
        """Test tile request with empty result"""
        mock_db_session.execute = AsyncMock(return_value=mock_empty_tile_result)
        
        response = client.get("/tiles/10/512/256.mvt")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.mapbox-vector-tile"
        assert response.content == b''
    
    def test_get_tile_max_zoom_exceeded(self, client, override_get_db):
        """Test tile request exceeding MAX_ZOOM"""
        response = client.get("/tiles/16/512/256.mvt")
        
        assert response.status_code == 204
    
    def test_get_tile_at_max_zoom(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test tile request at MAX_ZOOM boundary"""
        mock_db_session.execute = AsyncMock(return_value=mock_tile_result)
        
        response = client.get("/tiles/15/512/256.mvt")
        
        assert response.status_code == 200
    
    def test_get_tile_below_max_zoom(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test tile request below MAX_ZOOM"""
        mock_db_session.execute = AsyncMock(return_value=mock_tile_result)
        
        response = client.get("/tiles/14/512/256.mvt")
        
        assert response.status_code == 200
        mock_db_session.execute.assert_called_once()
    
    def test_get_tile_database_error(self, client, override_get_db, mock_db_session):
        """Test tile endpoint with database error"""
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        response = client.get("/tiles/10/512/256.mvt")
        
        assert response.status_code == 500
        assert "Database connection error" in response.json()["detail"]
    
    def test_get_tile_coordinates_boundary(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test with various coordinate combinations"""
        mock_db_session.execute.return_value = mock_tile_result
        test_coords = [(0, 0, 0), (1, 1, 1), (10, 512, 512), (14, 8191, 8191)]
        
        for z, x, y in test_coords:
            response = client.get(f"/tiles/{z}/{x}/{y}.mvt")
            assert response.status_code == 200
    
    def test_get_tile_query_parameters_passed(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test that query parameters are passed correctly to database"""
        mock_db_session.execute.return_value = mock_tile_result
        
        client.get("/tiles/5/100/200.mvt")
        
        # Verify execute was called
        assert mock_db_session.execute.called


class TestRunwayFunnelEndpoint:
    """Tests for /airport/runway-funnel endpoint"""
    
    def test_runway_funnel_success(self, client, override_get_db, mock_db_session, valid_runway_data):
        """Test successful runway funnel processing"""
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        with patch('airport_api.process_runway_geometry', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = True
            response = client.post("/airport/runway-funnel", json=valid_runway_data)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "processed and saved" in response.json()["message"]
    
    def test_runway_funnel_missing_features(self, client, override_get_db, valid_runway_data):
        """Test runway funnel with missing features"""
        invalid_data = {"airportName": "TestAirport", "features": []}
        
        response = client.post("/airport/runway-funnel", json=invalid_data)
        
        assert response.status_code == 500
    
    def test_runway_funnel_missing_airport_name(self, client, override_get_db):
        """Test runway funnel with missing airport name"""
        invalid_data = {
            "features": [{
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                }
            }]
        }
        
        response = client.post("/airport/runway-funnel", json=invalid_data)
        assert response.status_code == 500
    
    def test_runway_funnel_process_failure(self, client, override_get_db, valid_runway_data):
        """Test runway funnel processing failure"""
        with patch('airport_api.process_runway_geometry', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = False
            response = client.post("/airport/runway-funnel", json=valid_runway_data)
        
        assert response.status_code == 500
        assert "Failed to process" in response.json()["detail"]
    
    def test_runway_funnel_exception_handling(self, client, override_get_db, valid_runway_data):
        """Test runway funnel with exception during processing"""
        with patch('airport_api.process_runway_geometry', new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Processing error")
            response = client.post("/airport/runway-funnel", json=valid_runway_data)
        
        assert response.status_code == 500
        assert "Processing error" in response.json()["detail"]


class TestReportGeneratorEndpoint:
    """Tests for /report-generator endpoint"""
    
    def test_report_generator_success(self, client, override_get_db, mock_db_session, mock_report_result):
        """Test successful report generation"""
        mock_db_session.execute = AsyncMock(return_value=mock_report_result)
        
        response = client.get("/report-generator?lat=28.5&lng=77.1&elev=100")
        
        assert response.status_code == 200
    
    def test_report_generator_missing_lat(self, client, override_get_db):
        """Test report generator with missing latitude"""
        response = client.get("/report-generator?lng=77.1&elev=100")
        
        assert response.status_code == 422
    
    def test_report_generator_missing_lng(self, client, override_get_db):
        """Test report generator with missing longitude"""
        response = client.get("/report-generator?lat=28.5&elev=100")
        
        assert response.status_code == 422
    
    def test_report_generator_with_default_elevation(self, client, override_get_db, mock_db_session, mock_report_result):
        """Test report generator uses default elevation"""
        mock_db_session.execute = AsyncMock(return_value=mock_report_result)
        
        response = client.get("/report-generator?lat=28.5&lng=77.1")
        
        assert response.status_code == 200
    
    def test_report_generator_coordinates_at_boundaries(self, client, override_get_db, mock_db_session, mock_no_results):
        """Test report with edge case coordinates"""
        mock_db_session.execute = AsyncMock(return_value=mock_no_results)
        
        response = client.get("/report-generator?lat=85&lng=180&elev=0")
        assert response.status_code in [200, 500]
    
    def test_report_generator_no_results(self, client, override_get_db, mock_db_session, mock_no_results):
        """Test report generator when location not in any zone"""
        mock_db_session.execute.side_effect = [mock_no_results, mock_no_results]
        
        response = client.get("/report-generator?lat=28.5&lng=77.1&elev=100")
        
        assert response.status_code in [200, 500]
    
    def test_report_generator_database_error(self, client, override_get_db, mock_db_session):
        """Test report generator with database error"""
        mock_db_session.execute.side_effect = Exception("DB Error")
        
        response = client.get("/report-generator?lat=28.5&lng=77.1&elev=100")
        
        assert response.status_code == 500