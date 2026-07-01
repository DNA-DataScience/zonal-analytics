import pytest
import asyncio
from main import app, MAX_ZOOM


class TestAppConfiguration:
    """Tests for FastAPI app configuration"""
    
    def test_app_exists(self):
        """Test app instance exists"""
        assert app is not None
    
    def test_app_has_router(self):
        """Test app includes airport router"""
        routes = [route.path for route in app.routes]
        assert "/airport/runway-funnel" in routes
    
    def test_app_has_tile_endpoint(self):
        """Test app has tile endpoint"""
        routes = [route.path for route in app.routes]
        assert "/tiles/{z}/{x}/{y}.mvt" in routes
    
    def test_app_has_report_endpoint(self):
        """Test app has report generator endpoint"""
        routes = [route.path for route in app.routes]
        assert "/report-generator" in routes
    
    def test_cors_middleware_configured(self):
        """Test CORS middleware is added"""
        middleware_types = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_types
    
    def test_semaphore_initialized(self):
        """Test TILE_SEMAPHORE is initialized"""
        from main import get_tile_semaphore
        semaphore = get_tile_semaphore()
        assert semaphore is not None
        assert isinstance(semaphore, asyncio.Semaphore)
    
    def test_max_zoom_configured(self):
        """Test MAX_ZOOM constant is set"""
        assert MAX_ZOOM == 15
        assert isinstance(MAX_ZOOM, int)
    
    def test_app_routes_count(self):
        """Test app has expected number of routes"""
        routes = [route.path for route in app.routes]
        assert len(routes) >= 3  # tile, runway-funnel, report-generator