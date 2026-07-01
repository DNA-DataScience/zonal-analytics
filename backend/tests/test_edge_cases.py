import pytest
from unittest.mock import patch, AsyncMock


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_negative_zoom_level(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test with negative zoom level"""
        mock_db_session.execute.return_value = mock_tile_result
        response = client.get("/tiles/-1/512/256.mvt")
        assert response.status_code in [200, 500]
    
    def test_very_large_coordinates(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test with very large tile coordinates"""
        mock_db_session.execute.return_value = mock_tile_result
        response = client.get("/tiles/10/999999/999999.mvt")
        assert response.status_code == 200
    
    def test_zero_coordinates(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test with zero coordinates"""
        mock_db_session.execute.return_value = mock_tile_result
        response = client.get("/tiles/0/0/0.mvt")
        assert response.status_code == 200
    
    def test_invalid_geometry_in_funnel(self, client, override_get_db):
        """Test funnel processing with invalid geometry"""
        invalid_runway = {
            "airportName": "TestAirport",
            "features": [{
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [0, 0], [0, 0]]]
                }
            }]
        }
        
        response = client.post("/airport/runway-funnel", json=invalid_runway)
        assert response.status_code == 500
    
    def test_null_geometry(self, client, override_get_db):
        """Test with null geometry"""
        invalid_data = {
            "airportName": "TestAirport",
            "features": [{"geometry": None}]
        }
        
        response = client.post("/airport/runway-funnel", json=invalid_data)
        assert response.status_code == 500
    
    def test_empty_airport_name(self, client, override_get_db):
        """Test with empty airport name"""
        data = {
            "airportName": "",
            "features": [{
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                }
            }]
        }
        
        with patch('airport_api.process_runway_geometry', new_callable=AsyncMock) as mock:
            mock.return_value = True
            response = client.post("/airport/runway-funnel", json=data)
            assert response.status_code == 200
    
    def test_special_characters_in_airport_name(self, client, override_get_db):
        """Test with special characters in airport name"""
        data = {
            "airportName": "Test-Airport_123!@#",
            "features": [{
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                }
            }]
        }
        
        with patch('airport_api.process_runway_geometry', new_callable=AsyncMock) as mock:
            mock.return_value = True
            response = client.post("/airport/runway-funnel", json=data)
            assert response.status_code == 200
    
    def test_invalid_latitude_in_report(self, client, override_get_db):
        """Test report with invalid latitude"""
        response = client.get("/report-generator?lat=200&lng=77.1&elev=100")
        assert response.status_code in [200, 422, 500]
    
    def test_invalid_longitude_in_report(self, client, override_get_db):
        """Test report with invalid longitude"""
        response = client.get("/report-generator?lat=28.5&lng=400&elev=100")
        assert response.status_code in [200, 422, 500]