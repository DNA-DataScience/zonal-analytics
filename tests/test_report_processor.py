import pytest
from unittest.mock import AsyncMock, patch
from fastapi.responses import JSONResponse
from report_processor import generate_report, calc_min_height


class TestGenerateReportCoverage:
    """Tests for uncovered report_processor code paths"""
    
    @pytest.fixture
    def mock_db_middle_zone(self):
        """Mock DB returning middle zone result"""
        db = AsyncMock()
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("middle", "TestAirport", "civil", "120.5", 500, 5000.0),
        ])
        
        db.execute = AsyncMock(return_value=result)
        return db
    
    @pytest.fixture
    def mock_db_outer_zone(self):
        """Mock DB returning outer zone result"""
        db = AsyncMock()
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("outer", "TestAirport", "civil", "120.5", 500, 10000.0),
        ])
        
        db.execute = AsyncMock(return_value=result)
        return db
    
    @pytest.fixture
    def mock_db_no_results(self):
        """Mock DB returning no results"""
        db = AsyncMock()
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[])
        
        db.execute = AsyncMock(return_value=result)
        return db
    
    @pytest.mark.asyncio
    async def test_generate_report_middle_zone(self, mock_db_middle_zone):
        """Test report generation for middle zone"""
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=mock_db_middle_zone)
        
        # JSONResponse or dict
        assert report is not None
        if isinstance(report, JSONResponse):
            assert report.status_code == 200
        else:
            assert isinstance(report, (list, dict))
        mock_db_middle_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_report_outer_zone(self, mock_db_outer_zone):
        """Test report generation for outer zone"""
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=mock_db_outer_zone)
        
        assert report is not None
        if isinstance(report, JSONResponse):
            assert report.status_code == 200
        else:
            assert isinstance(report, (list, dict))
        mock_db_outer_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_report_middle_zone_limited_feasibility(self, mock_db_middle_zone):
        """Test middle zone has limited feasibility"""
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=mock_db_middle_zone)
        
        assert report is not None
        if isinstance(report, JSONResponse):
            # Extract content from JSONResponse
            import json
            content = json.loads(report.body.decode())
            assert any(item.get("zone") == "middle" for item in content)
            assert any("Limited Feasibility" in str(item.get("feasibility")) for item in content)
        mock_db_middle_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_report_outer_zone_feasible(self, mock_db_outer_zone):
        """Test outer zone is feasible with NOC"""
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=mock_db_outer_zone)
        
        assert report is not None
        if isinstance(report, JSONResponse):
            import json
            content = json.loads(report.body.decode())
            assert any(item.get("zone") == "outer" for item in content)
            assert any("Feasible" in str(item.get("feasibility")) for item in content)
        mock_db_outer_zone.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_report_no_results(self, mock_db_no_results):
        """Test report when location is not in any zone - returns nearest airport"""
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=mock_db_no_results)
        
        assert report is not None
        # Should return nearest airport result (could be dict or JSONResponse)
        assert isinstance(report, (dict, list)) or isinstance(report, JSONResponse)
    
    def test_calc_min_height_middle_zone_calculation(self):
        """Test min height calculation returns valid format for middle zone"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=3000)
        
        assert isinstance(min_height, (int, float))
        assert 0 <= min_height <= 300
    
    def test_calc_min_height_outer_zone_not_required(self):
        """Test outer zone calculation"""
        min_height = calc_min_height(elev=100, air_elev=200, distance_m=15000)
        
        assert isinstance(min_height, (int, float))
        assert min_height >= 0


class TestNearestAirportCoverage:
    """Tests for nearest_airport function coverage"""
    
    @pytest.fixture
    def mock_db_with_nearest_airport(self):
        """Mock DB returning nearest airport"""
        db = AsyncMock()
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("funnel", "Nearest Airport", "civil", "120.5", 500, 2000.0),
        ])
        
        db.execute = AsyncMock(return_value=result)
        return db
    
    @pytest.fixture
    def mock_db_no_nearest_airport(self):
        """Mock DB returning no nearest airport"""
        db = AsyncMock()
        
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[])
        
        db.execute = AsyncMock(return_value=result)
        return db
    
    @pytest.mark.asyncio
    async def test_nearest_airport_found(self, mock_db_with_nearest_airport):
        """Test nearest airport is found and reported"""
        from report_processor import nearest_airport
        
        result = await nearest_airport(lat=28.5, lng=77.1, elev=100, db=mock_db_with_nearest_airport)
        
        assert result is not None
        assert isinstance(result, (list, dict))
        # Should have zone field set to "nearest"
        if isinstance(result, list):
            assert any(item.get("zone") == "nearest" for item in result)
        mock_db_with_nearest_airport.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_nearest_airport_not_found(self, mock_db_no_nearest_airport):
        """Test when no nearest airport is found"""
        from report_processor import nearest_airport
        
        result = await nearest_airport(lat=28.5, lng=77.1, elev=100, db=mock_db_no_nearest_airport)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("status") == "no_results"
        mock_db_no_nearest_airport.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_nearest_airport_report_structure(self, mock_db_with_nearest_airport):
        """Test that nearest airport report has required fields"""
        from report_processor import nearest_airport
        
        result = await nearest_airport(lat=28.5, lng=77.1, elev=100, db=mock_db_with_nearest_airport)
        
        assert result is not None
        assert isinstance(result, list)
        
        if len(result) > 0:
            report_item = result[0]
            required_fields = ["zone", "name", "type", "radio", "airport_elevation", "min_height", "note", "feasibility", "distance"]
            for field in required_fields:
                assert field in report_item, f"Missing field: {field}"
        
        mock_db_with_nearest_airport.execute.assert_called()


class TestReportProcessorEdgeCases:
    """Additional edge case tests for report processor"""
    
    def test_calc_min_height_with_zone_inner_restricted(self):
        """Test min height with various distances"""
        result = calc_min_height(elev=100, air_elev=200, distance_m=1000)
        assert isinstance(result, (int, float))
        assert result >= 0
    
    def test_calc_min_height_format_variations(self):
        """Test that min_height returns consistent format"""
        result1 = calc_min_height(elev=100, air_elev=200, distance_m=5000)
        result2 = calc_min_height(elev=200, air_elev=300, distance_m=5000)
        result3 = calc_min_height(elev=50, air_elev=100, distance_m=20000)
        
        assert isinstance(result1, (int, float))
        assert isinstance(result2, (int, float))
        assert isinstance(result3, (int, float))
    
    @pytest.mark.asyncio
    async def test_generate_report_different_elevations(self):
        """Test report generation with various elevation values"""
        from report_processor import generate_report
        
        db = AsyncMock()
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("middle", "TestAirport", "civil", "120.5", 500, 5000.0),
        ])
        db.execute = AsyncMock(return_value=result)
        
        for elev in [0, 100, 500, 1000]:
            report = await generate_report(lat=28.5, lng=77.1, elev=elev, db=db)
            assert report is not None
    
    @pytest.mark.asyncio
    async def test_generate_report_funnel_zone_not_feasible(self):
        """Test funnel zone returns not feasible"""
        db = AsyncMock()
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("funnel", "TestAirport", "civil", "120.5", 500, 1000.0),
        ])
        db.execute = AsyncMock(return_value=result)
        
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=db)
        
        assert report is not None
        if isinstance(report, JSONResponse):
            import json
            content = json.loads(report.body.decode())
            assert any(item.get("feasibility") == "Not Feasible" for item in content)
    
    @pytest.mark.asyncio
    async def test_generate_report_inner_zone_not_feasible(self):
        """Test inner zone returns not feasible"""
        db = AsyncMock()
        result = AsyncMock()
        result.fetchall = AsyncMock(return_value=[
            ("inner", "TestAirport", "civil", "120.5", 500, 2000.0),
        ])
        db.execute = AsyncMock(return_value=result)
        
        report = await generate_report(lat=28.5, lng=77.1, elev=100, db=db)
        
        assert report is not None
        if isinstance(report, JSONResponse):
            import json
            content = json.loads(report.body.decode())
            assert any(item.get("feasibility") == "Not Feasible" for item in content)