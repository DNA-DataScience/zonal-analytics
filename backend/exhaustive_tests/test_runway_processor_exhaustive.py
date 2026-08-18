"""
Exhaustive tests for app/processors/reports/runway_processor.py

Covers:
  - create_arc_wedge: pure geometry helper
  - process_funnel: derives a funnel wedge pair from a runway polygon
  - process_runway_geometry: async DB read/union/difference/write workflow

process_runway_geometry has a notable quirk worth calling out up front:
line 111 of the source is

    results = await result.fetchall()

i.e. it *awaits* `.fetchall()`. In real SQLAlchemy (`AsyncSession.execute()`
already returns a fully-materialized, synchronous `Result` object -
`.fetchall()` on it is a normal blocking method, not a coroutine). Awaiting
a plain list raises `TypeError: object list can't be used in 'await'
expression'`, which the surrounding `except Exception` swallows, so against
a real SQLAlchemy AsyncSession this function would currently roll back and
return False on every call. Two test classes below cover this deliberately:
one that matches the code's literal expectation (async fetchall) to verify
the actual union/difference/insert-vs-update business logic, and one that
matches real SQLAlchemy's synchronous-`fetchall` behavior to document the
failure mode as it would occur in production.
"""
import time

import pytest
from shapely.geometry import Polygon, mapping

from app.processors.reports.runway_processor import (
    create_arc_wedge,
    process_funnel,
    process_runway_geometry,
)


# ============================================================================
# create_arc_wedge
# ============================================================================

class TestCreateArcWedge:
    def test_returns_a_polygon(self):
        wedge = create_arc_wedge((0, 0), radius_km=30, start_angle=90, arc_width=22)
        assert isinstance(wedge, Polygon)

    def test_polygon_ring_starts_and_ends_at_center_point(self):
        center = (77.5, 15.0)
        wedge = create_arc_wedge(center, radius_km=30, start_angle=45, arc_width=22, steps=10)
        coords = list(wedge.exterior.coords)
        assert coords[0] == pytest.approx(center)
        assert coords[-1] == pytest.approx(center)

    def test_point_count_matches_steps_plus_two(self):
        # points list = [center] + [steps arc points] + [center] = steps + 2
        wedge = create_arc_wedge((0, 0), radius_km=30, start_angle=0, arc_width=22, steps=15)
        coords = list(wedge.exterior.coords)
        # shapely may or may not de-duplicate the final closing coordinate;
        # assert on the pre-closure point list length instead of raw coords
        assert len(coords) in (16, 17)  # steps+2, possibly +1 for shapely's auto-close

    def test_default_steps_parameter_is_100(self):
        wedge_default = create_arc_wedge((0, 0), radius_km=30, start_angle=0, arc_width=22)
        wedge_explicit = create_arc_wedge((0, 0), radius_km=30, start_angle=0, arc_width=22, steps=100)
        assert len(list(wedge_default.exterior.coords)) == len(list(wedge_explicit.exterior.coords))

    def test_arc_points_stay_within_radius_of_center(self):
        center = (10.0, 20.0)
        radius_km = 30
        wedge = create_arc_wedge(center, radius_km=radius_km, start_angle=0, arc_width=22, steps=20)
        radius_deg = radius_km / 111.12
        for x, y in list(wedge.exterior.coords):
            dist = ((x - center[0]) ** 2 + (y - center[1]) ** 2) ** 0.5
            assert dist <= radius_deg + 1e-9

    def test_zero_radius_collapses_wedge_to_center_point(self):
        wedge = create_arc_wedge((5, 5), radius_km=0, start_angle=0, arc_width=22, steps=10)
        assert wedge.area == pytest.approx(0)

    def test_zero_arc_width_collapses_to_a_line(self):
        # start_angle - 0 == start_angle + 0 -> every arc point is identical
        wedge = create_arc_wedge((0, 0), radius_km=30, start_angle=45, arc_width=0, steps=10)
        assert wedge.area == pytest.approx(0)

    def test_full_360_arc_width_produces_nonzero_area(self):
        wedge = create_arc_wedge((0, 0), radius_km=30, start_angle=0, arc_width=360, steps=50)
        assert wedge.area > 0


# ============================================================================
# process_funnel
# ============================================================================

def _rectangle_runway(width_deg=0.01, length_deg=0.05, center=(78.0, 17.0)):
    """
    Build a simple axis-aligned rectangular "runway" polygon that is clearly
    longer along the x-axis, wrapped in the GeoJSON-like shape process_funnel
    expects (a dict with a "geometry" key readable by shapely.geometry.shape).
    """
    cx, cy = center
    hw, hl = width_deg / 2, length_deg / 2
    rect = Polygon(
        [
            (cx - hl, cy - hw),
            (cx + hl, cy - hw),
            (cx + hl, cy + hw),
            (cx - hl, cy + hw),
        ]
    )
    return {"geometry": mapping(rect)}


class TestProcessFunnel:
    def test_returns_a_polygon_geometry(self):
        runway = _rectangle_runway()
        funnel = process_funnel(runway)
        assert funnel.geom_type in ("Polygon", "MultiPolygon")
        assert funnel.is_valid or not funnel.is_empty

    def test_funnel_has_nonzero_area(self):
        runway = _rectangle_runway()
        funnel = process_funnel(runway)
        assert funnel.area > 0

    def test_funnel_is_centered_near_runway_centroid(self):
        center = (78.0, 17.0)
        runway = _rectangle_runway(center=center)
        funnel = process_funnel(runway)
        # both wedges are built from the same centre point, so the funnel's
        # bounding box should be roughly centered on the runway centroid
        minx, miny, maxx, maxy = funnel.bounds
        bbox_center = ((minx + maxx) / 2, (miny + maxy) / 2)
        assert bbox_center[0] == pytest.approx(center[0], abs=0.5)
        assert bbox_center[1] == pytest.approx(center[1], abs=0.5)

    def test_funnel_extends_roughly_30km_from_center_in_each_direction(self):
        center = (78.0, 17.0)
        runway = _rectangle_runway(center=center)
        funnel = process_funnel(runway)
        radius_deg = 30 / 111.12
        minx, miny, maxx, maxy = funnel.bounds
        # two opposing wedges should span roughly 2x the radius end-to-end
        # along whichever axis the funnel points
        span_x = maxx - minx
        span_y = maxy - miny
        assert max(span_x, span_y) == pytest.approx(2 * radius_deg, rel=0.15)

    def test_different_runway_orientations_produce_different_funnel_bounds(self):
        wide_runway = _rectangle_runway(width_deg=0.05, length_deg=0.005)  # long along y
        long_runway = _rectangle_runway(width_deg=0.005, length_deg=0.05)  # long along x
        funnel_a = process_funnel(wide_runway)
        funnel_b = process_funnel(long_runway)
        # These should be rotated ~90 degrees relative to each other, so
        # their bounding boxes should differ.
        assert funnel_a.bounds != funnel_b.bounds


# ============================================================================
# process_runway_geometry - async DB workflow
# ============================================================================

class AsyncFetchResult:
    """
    Matches what runway_processor.py's source code literally expects:
    `await result.fetchall()`. This does NOT match real SQLAlchemy's
    synchronous Result.fetchall() - see AsyncFetchResultRealisticFakeResult
    below for a fake that mirrors actual driver behavior instead.
    """

    def __init__(self, rows):
        self._rows = rows

    async def fetchall(self):
        return self._rows


class SyncFetchResult:
    """Mirrors real SQLAlchemy: fetchall() is a plain synchronous method."""

    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeAsyncSession:
    def __init__(self, select_rows, result_cls=AsyncFetchResult):
        self._select_rows = select_rows
        self._result_cls = result_cls
        self.executed = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, query, params=None):
        self.executed.append({"query": query, "params": params})
        if query is SELECT_QUERY_MARKER[0]:
            return self._result_cls(self._select_rows)
        return self._result_cls([])

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


# populated in setup below; module-level indirection lets FakeAsyncSession
# distinguish the SELECT call from UPDATE/INSERT calls without string-
# matching the compiled SQL text.
from app.processors.reports.runway_processor import SELECT_QUERY
SELECT_QUERY_MARKER = [SELECT_QUERY]


def _valid_wkb_hex_polygon(cx=78.0, cy=17.0, size=0.001):
    poly = Polygon(
        [(cx - size, cy - size), (cx + size, cy - size), (cx + size, cy + size), (cx - size, cy + size)]
    )
    return poly.wkb_hex


class TestProcessRunwayGeometryBusinessLogic:
    """
    Exercises the union/difference/insert-vs-update logic using a fake whose
    fetchall() is async, matching what the source code as written requires.
    """

    @pytest.mark.asyncio
    async def test_returns_true_and_commits_on_success(self):
        runway = _rectangle_runway()
        row = (_valid_wkb_hex_polygon(), "outer", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[row])

        result = await process_runway_geometry(runway, "Test Airport", db)

        assert result is True
        assert db.committed is True
        assert db.rolled_back is False

    @pytest.mark.asyncio
    async def test_inserts_new_funnel_zone_when_none_exists(self):
        runway = _rectangle_runway()
        row = (_valid_wkb_hex_polygon(), "outer", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[row])

        await process_runway_geometry(runway, "Test Airport", db)

        # 1 SELECT + 1 UPDATE (for the 'outer' row) + 1 INSERT (new funnel)
        insert_calls = [c for c in db.executed if c["params"] and c["params"].get("zone") == "funnel" and "lat" in c["params"]]
        assert len(insert_calls) == 1
        assert insert_calls[0]["params"]["name"] == "Test Airport"

    @pytest.mark.asyncio
    async def test_updates_existing_funnel_zone_instead_of_inserting(self):
        runway = _rectangle_runway()
        funnel_row = (_valid_wkb_hex_polygon(), "funnel", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[funnel_row])

        await process_runway_geometry(runway, "Test Airport", db)

        # Only UPDATE calls should carry a "zone"+"name" pair without "lat"/"type"
        insert_like_calls = [c for c in db.executed if c["params"] and "lat" in (c["params"] or {})]
        assert len(insert_like_calls) == 0

    @pytest.mark.asyncio
    async def test_non_funnel_non_inner_zone_gets_funnel_geometry_subtracted(self):
        runway = _rectangle_runway()
        row = (_valid_wkb_hex_polygon(), "middle", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[row])

        result = await process_runway_geometry(runway, "Test Airport", db)
        assert result is True
        update_calls = [c for c in db.executed if c["params"] and c["params"].get("zone") == "middle"]
        assert len(update_calls) == 1

    @pytest.mark.asyncio
    async def test_row_processing_order_affects_funnel_geometry_used_for_difference(self):
        """
        Documents an order-dependency in the source: `funnel_geometry` is
        mutated in place when an 'inner' zone row is processed
        (`funnel_geometry = funnel_geometry.difference(shapely_geom)`), and
        every subsequent non-funnel/non-inner row in the SAME call uses
        whatever `funnel_geometry` is at that point in the loop. So the
        resulting `middle`-zone geometry differs depending on whether the
        'inner' row appears before or after it in the query result order,
        even though both invocations describe the same physical zones.
        """
        inner_wkb = _valid_wkb_hex_polygon(cx=78.0, cy=17.0, size=0.02)
        middle_wkb = _valid_wkb_hex_polygon(cx=78.0, cy=17.0, size=0.03)

        inner_row = (inner_wkb, "inner", "civil", "VFR", 100.0, 17.0, 78.0)
        middle_row = (middle_wkb, "middle", "civil", "VFR", 100.0, 17.0, 78.0)

        runway = _rectangle_runway()

        db_inner_first = FakeAsyncSession(select_rows=[inner_row, middle_row])
        await process_runway_geometry(runway, "Test Airport", db_inner_first)
        middle_update_1 = next(
            c for c in db_inner_first.executed if c["params"] and c["params"].get("zone") == "middle"
        )

        db_middle_first = FakeAsyncSession(select_rows=[middle_row, inner_row])
        await process_runway_geometry(runway, "Test Airport", db_middle_first)
        middle_update_2 = next(
            c for c in db_middle_first.executed if c["params"] and c["params"].get("zone") == "middle"
        )

        # Both calls describe the same two DB rows, just in different order,
        # yet the geometry written for the 'middle' zone differs because of
        # the in-loop mutation of funnel_geometry described above.
        assert middle_update_1["params"]["geom"] != middle_update_2["params"]["geom"]

    @pytest.mark.asyncio
    async def test_db_execute_exception_triggers_rollback_and_returns_false(self):
        class ExplodingSession:
            async def execute(self, query, params=None):
                raise RuntimeError("connection lost")
                yield  # pragma: no cover

            async def commit(self):
                raise AssertionError("commit should not be called")

            async def rollback(self):
                self.rolled_back = True

        db = ExplodingSession()
        db.rolled_back = False
        runway = _rectangle_runway()

        result = await process_runway_geometry(runway, "Test Airport", db)

        assert result is False
        assert db.rolled_back is True

    @pytest.mark.asyncio
    async def test_malformed_geometry_bytes_triggers_rollback_and_returns_false(self):
        row = ("not-valid-wkb-hex", "outer", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[row])
        runway = _rectangle_runway()

        result = await process_runway_geometry(runway, "Test Airport", db)

        assert result is False
        assert db.rolled_back is True
        assert db.committed is False


class TestProcessRunwayGeometryRealisticSqlalchemyBehavior:
    """
    Uses a Result fake whose fetchall() is synchronous, matching how real
    SQLAlchemy's AsyncSession.execute() -> Result actually behaves. Against
    this more realistic fake, `await result.fetchall()` in the source
    raises TypeError (awaiting a plain list), which the function's own
    broad except-clause catches -> rollback -> False. This test exists to
    make that production-facing failure mode visible and regression-checked
    rather than silently relying on the "async fetchall" fake everywhere.
    """

    @pytest.mark.asyncio
    async def test_realistic_sync_fetchall_causes_silent_failure(self):
        row = (_valid_wkb_hex_polygon(), "outer", "civil", "VFR", 100.0, 17.0, 78.0)
        db = FakeAsyncSession(select_rows=[row], result_cls=SyncFetchResult)
        runway = _rectangle_runway()

        result = await process_runway_geometry(runway, "Test Airport", db)

        assert result is False
        assert db.rolled_back is True


# ============================================================================
# Response-time tracking
# ============================================================================

class TestRunwayProcessorResponseTime:
    def test_create_arc_wedge_latency(self, record_timing):
        iterations = 2000
        start = time.perf_counter()
        for _ in range(iterations):
            create_arc_wedge((78.0, 17.0), radius_km=30, start_angle=45, arc_width=22, steps=100)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        record_timing("create_arc_wedge", avg_ms, "ms/call")
        assert avg_ms < 5

    def test_process_funnel_latency(self, record_timing):
        runway = _rectangle_runway()
        iterations = 500
        start = time.perf_counter()
        for _ in range(iterations):
            process_funnel(runway)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        record_timing("process_funnel", avg_ms, "ms/call")
        assert avg_ms < 20

    @pytest.mark.asyncio
    async def test_process_runway_geometry_latency_with_many_zones(self, record_timing):
        rows = [
            (_valid_wkb_hex_polygon(size=0.001 * (i + 1)), zone, "civil", "VFR", 100.0, 17.0, 78.0)
            for i, zone in enumerate(["outer", "middle", "inner"] * 10)
        ]
        db = FakeAsyncSession(select_rows=rows)
        runway = _rectangle_runway()

        start = time.perf_counter()
        result = await process_runway_geometry(runway, "Test Airport", db)
        elapsed_ms = (time.perf_counter() - start) * 1000

        record_timing("process_runway_geometry[30 rows]", elapsed_ms, "ms")
        assert result is True
        assert elapsed_ms < 500
