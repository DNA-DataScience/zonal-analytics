import pytest
from airport_api import router


class TestAirportRouter:
    """Tests for airport router configuration"""
    
    def test_router_exists(self):
        """Test router is defined"""
        assert router is not None
    
    def test_router_has_funnel_route(self):
        """Test router has runway-funnel route"""
        routes = [route.path for route in router.routes]
        assert "/runway-funnel" in routes
    
    def test_router_route_methods(self):
        """Test router routes have correct HTTP methods"""
        for route in router.routes:
            if route.path == "/runway-funnel":
                assert "POST" in route.methods or not hasattr(route, 'methods')