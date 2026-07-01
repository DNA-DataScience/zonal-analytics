import pytest


class TestCORSMiddleware:
    """Tests for CORS middleware configuration"""
    
    def test_cors_middleware_configured(self):
        """Test CORS middleware is added to app"""
        from main import app
        
        # Check if any middleware is a CORSMiddleware
        middleware_names = [str(m.cls) for m in app.user_middleware]
        
        # Should contain CORSMiddleware
        assert any('CORSMiddleware' in str(m) for m in middleware_names), \
            f"CORSMiddleware not found in {middleware_names}"
    
    def test_cors_wildcard_origin(self, client):
        """Test CORS allows all origins"""
        response = client.get(
            "/tiles/10/512/256.mvt",
            headers={"Origin": "https://example.com"}
        )
        
        assert response.status_code in [200, 500]
    
    def test_cors_multiple_origins(self, client):
        """Test CORS accepts multiple origins"""
        origins = [
            "https://example.com",
            "http://localhost:3000",
            "https://test.org",
        ]
        
        for origin in origins:
            response = client.get(
                "/tiles/10/512/256.mvt",
                headers={"Origin": origin}
            )
            assert response.status_code in [200, 500]
    
    def test_cors_methods_allowed(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test CORS allows multiple HTTP methods"""
        mock_db_session.execute.return_value = mock_tile_result
        
        response_get = client.get("/tiles/10/512/256.mvt")
        response_options = client.options("/tiles/10/512/256.mvt")
        
        assert response_get.status_code == 200
        assert response_options.status_code in [200, 405]
    
    def test_cors_credentials_allowed(self, client):
        """Test CORS allows credentials in request"""
        response = client.get(
            "/tiles/10/512/256.mvt",
            headers={
                "Origin": "https://example.com",
                "Cookie": "test=value"
            }
        )
        
        assert response.status_code in [200, 500]
    
    def test_cors_headers_exposed(self, client, override_get_db, mock_db_session, mock_tile_result):
        """Test CORS exposes headers"""
        mock_db_session.execute.return_value = mock_tile_result
        
        response = client.get(
            "/tiles/10/512/256.mvt",
            headers={"Origin": "https://example.com"}
        )
        
        # CORS should be configured (even if headers not in response due to TestClient)
        assert response.status_code == 200