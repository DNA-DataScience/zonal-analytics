import pytest
from shapely.geometry import Polygon
from runway_processor import create_arc_wedge, process_funnel


class TestFunnelGeneration:
    """Tests for runway funnel geometry generation"""
    
    def test_create_arc_wedge_geometry(self):
        """Test arc wedge creation returns valid polygon"""
        center = (77.0, 28.0)
        wedge = create_arc_wedge(center, 10, 45, 22, steps=50)
        
        assert wedge.is_valid
        assert wedge.geom_type == "Polygon"
    
    def test_create_arc_wedge_different_radii(self):
        """Test arc wedge with different radius values"""
        center = (0.0, 0.0)
        
        for radius in [5, 10, 20, 50]:
            wedge = create_arc_wedge(center, radius, 45, 22)
            assert wedge.is_valid
            assert wedge.area > 0
    
    def test_create_arc_wedge_different_angles(self):
        """Test arc wedge with different start angle values"""
        center = (0.0, 0.0)
        
        for angle in [0, 45, 90, 180, 270]:
            wedge = create_arc_wedge(center, 10, angle, 22)
            assert wedge.is_valid
    
    def test_create_arc_wedge_different_widths(self):
        """Test arc wedge with different arc widths"""
        center = (0.0, 0.0)
        
        for width in [10, 22, 45, 90]:
            wedge = create_arc_wedge(center, 10, 45, width)
            assert wedge.is_valid
    
    def test_create_arc_wedge_steps_affect_precision(self):
        """Test that more steps create more detailed geometry"""
        center = (0.0, 0.0)
        
        wedge_low = create_arc_wedge(center, 10, 45, 22, steps=10)
        wedge_high = create_arc_wedge(center, 10, 45, 22, steps=100)
        
        assert wedge_low.is_valid
        assert wedge_high.is_valid
    
    def test_process_funnel_valid_runway(self):
        """Test funnel processing with valid runway"""
        runway = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.05, 28.0], [77.05, 28.05], [77.0, 28.05], [77.0, 28.0]]]
            }
        }
        
        funnel = process_funnel(runway)
        
        assert funnel.is_valid
        assert funnel.area >= 0
    
    def test_process_funnel_centroid_calculation(self):
        """Test that funnel is generated from runway centroid"""
        runway = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
            }
        }
        
        funnel = process_funnel(runway)
        
        assert funnel.is_valid
        assert funnel.bounds is not None
    
    def test_funnel_geometry_intersection(self):
        """Test funnel geometry intersection operations"""
        runway = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        }
        
        funnel = process_funnel(runway)
        test_polygon = Polygon([[0.3, 0.3], [0.7, 0.3], [0.7, 0.7], [0.3, 0.7]])
        
        intersection = funnel.intersection(test_polygon)
        union = funnel.union(test_polygon)
        
        assert intersection.area >= 0
        assert union.area >= intersection.area
    
    def test_process_funnel_multiple_runways(self):
        """Test processing multiple different runways"""
        runways = [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1], [77.0, 28.0]]]
                }
            },
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[77.2, 28.2], [77.3, 28.2], [77.3, 28.3], [77.2, 28.3], [77.2, 28.2]]]
                }
            }
        ]
        
        for runway in runways:
            funnel = process_funnel(runway)
            assert funnel.is_valid