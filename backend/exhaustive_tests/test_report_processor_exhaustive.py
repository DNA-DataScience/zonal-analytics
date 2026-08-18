"""
Exhaustive tests for app/processors/reports/report_processor.py

generate_report() runs four DB queries (airport, MoD, forest, inner-zone),
falls back to a "nearest airport" lookup when nothing intersects, and
assembles everything into a combined + per-layer report. These tests use a
FakeSession/FakeResult pair (same shape as the project's existing
tests/test_report_processor.py) so no real database is required, and drive
every branch: empty results, mixed results, each query's error path, and
the nearest-airport fallback (including its own error path).

A dedicated response-time section at the bottom measures generate_report's
latency as the number of intersecting zones grows, since that is the
function actually exposed to callers over HTTP.
"""
import json
import time

import pytest
from fastapi import HTTPException

from app.processors.reports.report_processor import (
    generate_report,
    get_nearest_airport_data,
)


# ============================================================================
# Fakes - mirrors the pattern used in tests/test_report_processor.py and
# tests/test_batch_processor.py so this file stays consistent with the rest
# of the suite.
# ============================================================================

class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    """
    Returns one canned result per call to execute(), in call order.
    generate_report always queries in this order: airport, mod, forest,
    inner_zones, and then (only if all four are empty) nearest-airport.
    """

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    async def execute(self, query, params):
        self.calls.append({"query": query, "params": params})
        return FakeResult(self._results.pop(0))


class FailingSession:
    """Raises on the Nth execute() call (0-indexed); returns FakeResult otherwise."""

    def __init__(self, results, fail_at_index, error=None):
        self._results = list(results)
        self._fail_at_index = fail_at_index
        self._error = error or RuntimeError("boom")
        self._call_count = 0
        self.calls = []

    async def execute(self, query, params):
        self.calls.append({"query": query, "params": params})
        idx = self._call_count
        self._call_count += 1
        if idx == self._fail_at_index:
            raise self._error
        return FakeResult(self._results.pop(0))


AIRPORT_ROW = ("outer", "Test Airport", "civil", "VFR", 100.0, None, 25000.0)
MOD_ROW = ("NOC", "Test MoD Zone", "restricted")
FOREST_ROW = ("Test Forest",)
INNER_ROW = ("Reservoir", "Test Reservoir", "TS", "Telangana")
NEAREST_ROW = ("nearest", "Nearest Airport", "civil", "VFR", 50.0, None, 100000.0)


# ============================================================================
# No-results / nearest-airport fallback paths
# ============================================================================

class TestGenerateReportNoResultsAndFallback:
    @pytest.mark.asyncio
    async def test_all_empty_and_no_nearest_airport_returns_no_results_status(self):
        db = FakeSession(results=[[], [], [], [], []])
        response = await generate_report(20.0, 73.0, db=db)
        body = json.loads(response.body)
        assert body == {"status": "no_results", "message": "No zones or airports found"}
        assert len(db.calls) == 5  # 4 primary queries + nearest fallback

    @pytest.mark.asyncio
    async def test_all_empty_falls_back_to_nearest_airport(self):
        db = FakeSession(results=[[], [], [], [], [NEAREST_ROW]])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        assert len(report) == 1
        assert report[0]["layer"] == "airport"
        assert report[0]["zone"] == "nearest"
        assert report[0]["name"] == "Nearest Airport"
        assert report[0]["feasibility"] == "Feasible"
        # no "combined" entry should be produced when there are no intersecting zones
        assert all(r["layer"] != "combined" for r in report)

    @pytest.mark.asyncio
    async def test_partial_results_does_not_trigger_nearest_airport_lookup(self):
        # mod zones present -> nearest-airport branch must NOT fire, so only
        # 4 execute() calls should happen, not 5.
        db = FakeSession(results=[[], [MOD_ROW], [], []])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        assert len(db.calls) == 4
        assert report[0]["layer"] == "combined"
        assert any(r["layer"] == "mod" for r in report)


# ============================================================================
# Combined analysis + report ordering
# ============================================================================

class TestGenerateReportOrderingAndContent:
    @pytest.mark.asyncio
    async def test_combined_is_first_followed_by_airport_mod_forest_inner(self):
        db = FakeSession(
            results=[[AIRPORT_ROW], [MOD_ROW], [FOREST_ROW], [INNER_ROW]]
        )
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        layers_in_order = [r["layer"] for r in report]
        assert layers_in_order == ["combined", "airport", "mod", "forest", "inner_zones"]

    @pytest.mark.asyncio
    async def test_inner_zone_forces_not_feasible_combined_result(self):
        db = FakeSession(results=[[], [], [], [INNER_ROW]])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        assert report[0]["layer"] == "combined"
        assert report[0]["feasibility"] == "No"
        assert report[0]["total_inner_zone_zones"] == 1
        assert report[-1]["layer"] == "inner_zones"
        assert report[-1]["zone"] == "Reservoir"

    @pytest.mark.asyncio
    async def test_only_airport_zone_produces_correct_combined_feasibility(self):
        db = FakeSession(results=[[AIRPORT_ROW], [], [], []])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        assert report[0]["feasibility"] == "Yes"  # "outer" zone alone -> Yes
        assert report[0]["total_airport_zones"] == 1
        assert report[0]["total_mod_zones"] == 0

    @pytest.mark.asyncio
    async def test_multiple_airport_rows_use_most_restrictive_for_combined(self):
        funnel_row = ("funnel", "Close Airport", "civil", "VFR", 100.0, None, 500.0)
        outer_row = ("outer", "Far Airport", "civil", "VFR", 100.0, None, 30000.0)
        db = FakeSession(results=[[outer_row, funnel_row], [], [], []])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        assert report[0]["feasibility"] == "No"  # funnel wins over outer
        assert report[0]["total_airport_zones"] == 2
        # both individual airport reports still present, in query-row order
        airport_layer_entries = [r for r in report if r["layer"] == "airport"]
        assert [e["name"] for e in airport_layer_entries] == ["Far Airport", "Close Airport"]

    @pytest.mark.asyncio
    async def test_elevation_parameter_flows_into_middle_zone_min_height(self):
        middle_row = ("middle", "Mid Airport", "civil", "VFR", 200.0, None, 8000.0)
        db = FakeSession(results=[[middle_row], [], [], []])
        response = await generate_report(20.0, 73.0, elev=50.0, db=db)
        report = json.loads(response.body)

        airport_entry = next(r for r in report if r["layer"] == "airport")
        expected = min(200.0 + (45 + 0.05 * (8000.0 - 4000)) - 50.0, 300)
        assert airport_entry["min_height"] == f"{expected:.1f}m"

    @pytest.mark.asyncio
    async def test_elevation_defaults_to_zero_when_omitted(self):
        middle_row = ("middle", "Mid Airport", "civil", "VFR", 200.0, None, 8000.0)
        db = FakeSession(results=[[middle_row], [], [], []])
        response = await generate_report(20.0, 73.0, db=db)  # no elev kwarg
        report = json.loads(response.body)

        airport_entry = next(r for r in report if r["layer"] == "airport")
        expected = min(200.0 + (45 + 0.05 * (8000.0 - 4000)) - 0.0, 300)
        assert airport_entry["min_height"] == f"{expected:.1f}m"

    @pytest.mark.asyncio
    async def test_query_params_include_lat_and_lon_for_every_call(self):
        db = FakeSession(results=[[], [], [], []])
        await generate_report(20.5, 73.5, db=db)
        for call in db.calls:
            assert call["params"] == {"lat": 20.5, "lon": 73.5}

    @pytest.mark.asyncio
    async def test_forest_row_without_name_defaults_to_unknown_forest(self):
        db = FakeSession(results=[[], [], [(None,)], []])
        response = await generate_report(20.0, 73.0, db=db)
        report = json.loads(response.body)

        forest_entry = next(r for r in report if r["layer"] == "forest")
        assert forest_entry["name"] == "Unknown Forest"


# ============================================================================
# Error handling - each of the four primary queries
# ============================================================================

class TestGenerateReportErrorHandling:
    @pytest.mark.asyncio
    async def test_airport_query_failure_raises_500(self):
        db = FailingSession(results=[[], [], []], fail_at_index=0, error=RuntimeError("airport db down"))
        with pytest.raises(HTTPException) as exc_info:
            await generate_report(20.0, 73.0, db=db)
        assert exc_info.value.status_code == 500
        assert "airport db down" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_mod_query_failure_raises_500(self):
        db = FailingSession(results=[[], [], []], fail_at_index=1, error=RuntimeError("mod db down"))
        with pytest.raises(HTTPException) as exc_info:
            await generate_report(20.0, 73.0, db=db)
        assert exc_info.value.status_code == 500
        assert "mod db down" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_forest_query_failure_raises_500(self):
        db = FailingSession(results=[[], [], []], fail_at_index=2, error=RuntimeError("forest db down"))
        with pytest.raises(HTTPException) as exc_info:
            await generate_report(20.0, 73.0, db=db)
        assert exc_info.value.status_code == 500
        assert "forest db down" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_inner_zones_query_failure_raises_500(self):
        db = FailingSession(results=[[], [], []], fail_at_index=3, error=RuntimeError("inner zones db down"))
        with pytest.raises(HTTPException) as exc_info:
            await generate_report(20.0, 73.0, db=db)
        assert exc_info.value.status_code == 500
        assert "inner zones db down" in str(exc_info.value.detail)


# ============================================================================
# get_nearest_airport_data (tested directly, not just through generate_report)
# ============================================================================

class TestGetNearestAirportData:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_rows_found(self):
        db = FakeSession(results=[[]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_database_exception_instead_of_raising(self):
        # Unlike the four primary queries, get_nearest_airport_data
        # deliberately swallows the exception and returns None so that a
        # nearest-airport lookup failure doesn't take down the whole report.
        class ExplodingSession:
            async def execute(self, query, params):
                raise RuntimeError("connection reset")

        result = await get_nearest_airport_data(20.0, 73.0, db=ExplodingSession())
        assert result is None

    @pytest.mark.asyncio
    async def test_vfr_autosettle_yes_beyond_20km(self):
        row = ("nearest", "Airport A", "civil", "VFR", 50.0, None, 25000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["autoSettle"] == "Yes"

    @pytest.mark.asyncio
    async def test_vfr_autosettle_no_within_20km(self):
        row = ("nearest", "Airport A", "civil", "VFR", 50.0, None, 5000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["autoSettle"] == "No"

    @pytest.mark.asyncio
    async def test_ifr_autosettle_yes_beyond_56km(self):
        row = ("nearest", "Airport A", "civil", "IFR", 50.0, None, 60000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["autoSettle"] == "Yes"

    @pytest.mark.asyncio
    async def test_crz_none_defaults_to_na_string(self):
        row = ("nearest", "Airport A", "civil", "VFR", 50.0, None, 25000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["cczm"] == "na"

    @pytest.mark.asyncio
    async def test_crz_value_is_passed_through(self):
        row = ("nearest", "Airport A", "civil", "VFR", 50.0, "Mumbai", 25000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["cczm"] == "Mumbai"

    @pytest.mark.asyncio
    async def test_static_fields_are_always_the_same(self):
        row = ("nearest", "Airport A", "civil", "VFR", 50.0, None, 25000.0)
        db = FakeSession(results=[[row]])
        result = await get_nearest_airport_data(20.0, 73.0, db=db)
        assert result["feasibility"] == "Feasible"
        assert result["min_height"] == "Not Required"
        assert result["note"] == "Auto Settle only viable if height of WTG is 150m or less"
        assert result["layer"] == "airport"
        assert result["zone"] == "nearest"


# ============================================================================
# Response-time tracking
# ============================================================================

class TestGenerateReportResponseTime:
    """
    generate_report is the function directly behind the point-lookup API
    endpoint, so its latency (excluding real network/DB time, which the
    fakes remove) reflects the pure Python-side processing cost: row->dict
    conversion, report building, and combined-analysis aggregation. This
    tracks how that cost scales with the number of intersecting zones.
    """

    @pytest.mark.asyncio
    async def test_response_time_with_no_intersecting_zones(self, record_timing):
        db = FakeSession(results=[[], [], [], [], [NEAREST_ROW]])
        start = time.perf_counter()
        await generate_report(20.0, 73.0, db=db)
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_timing("generate_report[no zones, nearest fallback]", elapsed_ms, "ms")
        assert elapsed_ms < 50

    @pytest.mark.asyncio
    async def test_response_time_with_single_zone_per_layer(self, record_timing):
        db = FakeSession(results=[[AIRPORT_ROW], [MOD_ROW], [FOREST_ROW], [INNER_ROW]])
        start = time.perf_counter()
        await generate_report(20.0, 73.0, db=db)
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_timing("generate_report[1 zone per layer]", elapsed_ms, "ms")
        assert elapsed_ms < 50

    @pytest.mark.asyncio
    async def test_response_time_with_many_overlapping_zones(self, record_timing):
        # A dense metro area might intersect dozens of airport funnel/inner/
        # middle/outer polygons and multiple MoD/forest/inner-zone layers at once.
        airport_rows = [
            ("outer", f"Airport {i}", "civil", "VFR", 100.0 + i, None, 20000.0 + i)
            for i in range(200)
        ]
        mod_rows = [("NOC", f"Mod Zone {i}", "restricted") for i in range(200)]
        forest_rows = [(f"Forest {i}",) for i in range(200)]
        inner_rows = [("Sanctuary", f"Inner {i}", "TS", "Telangana") for i in range(200)]

        db = FakeSession(results=[airport_rows, mod_rows, forest_rows, inner_rows])
        start = time.perf_counter()
        response = await generate_report(20.0, 73.0, db=db)
        elapsed_ms = (time.perf_counter() - start) * 1000

        record_timing("generate_report[200 zones x 4 layers]", elapsed_ms, "ms")
        report = json.loads(response.body)
        assert report[0]["total_airport_zones"] == 200
        assert elapsed_ms < 500
