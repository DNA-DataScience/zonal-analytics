import pytest
from report_processor import calc_min_height


class TestReportGenerator:
    """Tests for report generation logic"""
    
    def test_calc_min_height_funnel_zone(self):
        """Test minimum height calculation for funnel zone"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=5000)
        
        assert isinstance(min_height, (int, float))
        assert min_height <= 300
    
    def test_calc_min_height_inner_zone(self):
        """Test minimum height for inner zone (restricted)"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=2000)
        
        assert min_height <= 300
        assert isinstance(min_height, (int, float))
    
    def test_calc_min_height_outer_zone(self):
        """Test minimum height for outer zone"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=10000)
        
        assert isinstance(min_height, (int, float))
    
    def test_calc_min_height_zero_distance(self):
        """Test min height with zero distance (at airport)"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=0)
        
        assert isinstance(min_height, (int, float))
        assert min_height >= 0
    
    def test_calc_min_height_elevation_differences(self):
        """Test min height with various elevation differences"""
        cases = [
            (0, 100, 5000),
            (500, 200, 5000),
            (1000, 500, 5000),
            (100, 1000, 5000),
        ]
        
        for elev, air_elev, dist in cases:
            result = calc_min_height(elev, air_elev, dist)
            assert isinstance(result, (int, float))
            assert result <= 300
    
    def test_calc_min_height_distance_variations(self):
        """Test min height across distance spectrum"""
        distances = [1000, 4000, 5000, 10000, 50000]
        
        for distance in distances:
            result = calc_min_height(elev=100, air_elev=200, distance_m=distance)
            assert isinstance(result, (int, float))
    
    def test_calc_min_height_consistency(self):
        """Test that same inputs produce same output"""
        result1 = calc_min_height(elev=100, air_elev=200, distance_m=5000)
        result2 = calc_min_height(elev=100, air_elev=200, distance_m=5000)
        
        assert result1 == result2
    
    def test_calc_min_height_boundary_values(self):
        """Test min height with boundary values"""
        # Test at 300m cap
        result_high = calc_min_height(elev=0, air_elev=500, distance_m=1000)
        assert result_high <= 300
        
        # Test at minimum
        result_low = calc_min_height(elev=1000, air_elev=500, distance_m=50000)
        assert result_low > 0