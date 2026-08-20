import pytest
from starlette.requests import Request
from datetime import datetime, timezone

from app.api import analytics


class FakeResult:
    def __init__(self, value=None):
        self._value = value

    def fetchone(self):
        return self._value


class FakeSession:
    def __init__(self, value=None):
        self.value = value
        self.calls = []
        self.commit_calls = 0
        self.rollback_calls = 0

    async def execute(self, query, params):
        self.calls.append({"query": query, "params": params})
        return FakeResult(self.value)

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


def _request() -> Request:
    return Request({"type": "http", "headers": []})


@pytest.mark.asyncio
async def test_heartbeat_is_disabled_and_skips_db_writes():
    db = FakeSession()
    payload = analytics.HeartbeatRequest(
        session_id="11111111-1111-1111-1111-111111111111",
        anonymous_id="22222222-2222-2222-2222-222222222222",
    )

    response = await analytics.heartbeat(payload, _request(), db)

    assert response == {"status": "ok", "persisted": False, "disabled": True}
    assert db.calls == []
    assert db.commit_calls == 0


@pytest.mark.asyncio
async def test_event_is_disabled_and_skips_db_writes():
    db = FakeSession()
    payload = analytics.EventRequest(
        session_id="11111111-1111-1111-1111-111111111111",
        event_type="map_interaction",
        endpoint=None,
        metadata={"action": "map_loaded"},
    )

    response = await analytics.event(payload, _request(), db)

    assert response == {"status": "ok", "persisted": False, "disabled": True}
    assert db.calls == []
    assert db.commit_calls == 0


@pytest.mark.asyncio
async def test_session_end_handles_timezone_aware_started_at():
    started_at = datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc)
    db = FakeSession(value=(started_at, started_at))
    payload = analytics.SessionEndRequest(
        session_id="11111111-1111-1111-1111-111111111111",
        anonymous_id="22222222-2222-2222-2222-222222222222",
    )

    response = await analytics.session_end(payload, _request(), db)

    assert response["status"] == "ok"
    assert isinstance(response["duration_seconds"], int)
