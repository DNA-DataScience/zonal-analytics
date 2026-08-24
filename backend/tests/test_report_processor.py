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
async def test_report_uat_mode_excludes_forest_and_inner_layers():
    response = await generate_report(
        20.0,
        73.0,
        db=FakeSession(
            results=[[("outer", "Pune Airport", "Civil", 4500, 560, None, 9000.0)], []]
        ),
    )

    report = json.loads(response.body)
    assert report[0]["layer"] == "combined"
    assert report[0]["total_forest_zones"] == 0
    assert report[0]["total_inner_zone_zones"] == 0
    assert all(item["layer"] in {"combined", "airport", "mod"} for item in report)
