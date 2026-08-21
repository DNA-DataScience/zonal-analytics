import json

import pytest

from app.processors.reports.report_processor import generate_report


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    async def execute(self, query, params):
        self.calls.append({"query": query, "params": params})
        return FakeResult(self._results.pop(0))


@pytest.mark.asyncio
async def test_report_includes_inner_zone_and_returns_not_feasible():
    response = await generate_report(
        20.0,
        73.0,
        db=FakeSession(
            results=[[], [], [], [("Reservoir", "Nagarjuna Sagar", "TS", "Telangana")]]
        ),
    )

    report = json.loads(response.body)
    assert report[0]["layer"] == "combined"
    assert report[0]["feasibility"] == "No"
    assert report[0]["total_inner_zone_zones"] == 1
    assert report[-1]["layer"] == "inner_zones"
    assert report[-1]["zone"] == "Reservoir"
