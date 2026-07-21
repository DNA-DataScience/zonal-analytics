import pytest
from fastapi import HTTPException
from app.api import tiles


class FakeResult:
    def __init__(self, value=None):
        self._value = value

    def scalar(self):
        return self._value


class FakeSession:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error
        self.calls = []

    async def execute(self, query, params):
        self.calls.append({"query": query, "params": params})
        if self.error:
            raise self.error
        return FakeResult(self.value)


@pytest.mark.asyncio
async def test_inner_zones_tile_returns_mvt_bytes():
    db = FakeSession(value=b"tile-bytes")
    response = await tiles.get_inner_zones_tile(z=8, x=120, y=90, db=db)

    assert response.status_code == 200
    assert response.media_type == "application/vnd.mapbox-vector-tile"
    assert response.body == b"tile-bytes"
    assert db.calls[0]["params"] == {"z": 8, "x": 120, "y": 90}


@pytest.mark.asyncio
async def test_inner_zones_tile_returns_empty_mvt_when_query_is_empty():
    db = FakeSession(value=None)
    response = await tiles.get_inner_zones_tile(z=8, x=120, y=90, db=db)

    assert response.status_code == 200
    assert response.media_type == "application/vnd.mapbox-vector-tile"
    assert response.body == b""


@pytest.mark.asyncio
async def test_inner_zones_tile_skips_database_above_max_zoom():
    db = FakeSession(value=b"should-not-be-used")
    response = await tiles.get_inner_zones_tile(
        z=tiles.MAX_ZOOM + 1, x=120, y=90, db=db
    )

    assert response.status_code == 204
    assert db.calls == []


@pytest.mark.asyncio
async def test_inner_zones_tile_translates_database_error_to_500():
    db = FakeSession(error=RuntimeError("db failed"))
    with pytest.raises(HTTPException, match="db failed") as exc:
        await tiles.get_inner_zones_tile(z=8, x=120, y=90, db=db)

    assert exc.value.status_code == 500
