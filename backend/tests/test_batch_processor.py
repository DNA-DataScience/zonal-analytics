import pytest

from app.processors.batches.batch_processor import (
    generate_batch_report,
    save_batch_to_csv,
)


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


def test_batch_csv_includes_inner_zone_column():
    csv_content, _ = save_batch_to_csv(
        [{"id": 1, "lat": 20, "lon": 73}],
        [
            {
                "pid": 1,
                "feasibility": "No",
                "most_restrictive_airport": "No zones exist",
                "most_restrictive_mod": "No zones exist",
                "most_restrictive_forest": "No zones exist",
                "most_restrictive_inner_zone": "Reservoir - Nagarjuna Sagar",
            }
        ],
    )

    assert "Most Restrictive Inner Zone" in csv_content.splitlines()[0]
    assert "Reservoir - Nagarjuna Sagar" in csv_content


@pytest.mark.asyncio
async def test_batch_inner_zone_forces_no_feasibility():
    db = FakeSession(
        results=[
            [],  # airport zones
            [],  # mod zones
            [],  # forest zones
            [(1, "Reservoir", "Nagarjuna Sagar", "TS", "Telangana")],  # inner zones
        ]
    )

    result = await generate_batch_report([{"id": 1, "lat": 20, "lon": 73}], db)

    assert ",No," in result["csv_content"]
    assert "Reservoir - Nagarjuna Sagar" in result["csv_content"]
    assert len(db.calls) == 4
