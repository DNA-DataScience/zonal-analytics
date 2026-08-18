import sys
import json
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ============================================================================
# RESPONSE TIME TRACKING
# ============================================================================
# Every test's wall-clock duration is captured automatically (via pytest's
# built-in TestReport.duration) and written to a JSON artifact at the end of
# the run, plus a sorted summary table printed to the terminal. This applies
# to the whole suite so the feasibility-engine and report-generator tests are
# timed the same way as everything else, with no per-test boilerplate needed.
#
# Output artifact: tests/.perf/response_times_<timestamp>.json
# ============================================================================

_TIMINGS = []  # list of dicts: {"nodeid", "duration_ms", "outcome"}
_NAMED_TIMINGS = []  # list of dicts: {"nodeid", "label", "value", "unit"}


@pytest.fixture
def record_timing(request):
    """
    Lets a test record a *named* measurement (e.g. "determine_feasibility",
    average call latency in microseconds) in addition to pytest's own
    whole-test duration. Useful for pinpointing which specific operation
    inside a test is slow, rather than just knowing the test as a whole
    took N ms.

    Usage:
        def test_something(record_timing):
            ...
            record_timing("my_operation", 12.3, "ms")
    """

    def _record(label, value, unit="ms"):
        _NAMED_TIMINGS.append(
            {
                "nodeid": request.node.nodeid,
                "label": label,
                "value": round(value, 4),
                "unit": unit,
            }
        )

    return _record


def pytest_runtest_logreport(report):
    if report.when == "call":
        _TIMINGS.append(
            {
                "nodeid": report.nodeid,
                "duration_ms": round(report.duration * 1000, 3),
                "outcome": report.outcome,
            }
        )


def pytest_sessionfinish(session, exitstatus):
    if not _TIMINGS:
        return

    out_dir = Path(__file__).resolve().parent / ".perf"
    out_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"response_times_{ts}.json"

    ordered = sorted(_TIMINGS, key=lambda t: t["duration_ms"], reverse=True)
    total_ms = sum(t["duration_ms"] for t in _TIMINGS)
    summary = {
        "total_tests": len(_TIMINGS),
        "total_duration_ms": round(total_ms, 3),
        "average_duration_ms": round(total_ms / len(_TIMINGS), 3),
        "slowest": ordered[:10],
        "all_timings": ordered,
    }
    out_file.write_text(json.dumps(summary, indent=2))

    named_file = None
    if _NAMED_TIMINGS:
        named_file = out_dir / f"named_timings_{ts}.json"
        named_file.write_text(json.dumps(_NAMED_TIMINGS, indent=2))

    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal is not None:
        terminal.write_line("")
        terminal.write_line("=" * 70)
        terminal.write_line("RESPONSE TIME SUMMARY (slowest 10 tests)")
        terminal.write_line("=" * 70)
        for t in ordered[:10]:
            terminal.write_line(f"{t['duration_ms']:>10.3f} ms  {t['outcome']:<8} {t['nodeid']}")
        terminal.write_line("-" * 70)
        terminal.write_line(
            f"Total: {summary['total_tests']} tests, "
            f"{summary['total_duration_ms']:.3f} ms combined, "
            f"{summary['average_duration_ms']:.3f} ms average"
        )
        terminal.write_line(f"Full report written to: {out_file}")

        if _NAMED_TIMINGS:
            terminal.write_line("")
            terminal.write_line("NAMED PERFORMANCE SCENARIOS")
            terminal.write_line("-" * 70)
            for nt in _NAMED_TIMINGS:
                terminal.write_line(f"{nt['label']:<45} {nt['value']:>10} {nt['unit']}")
            terminal.write_line(f"Full report written to: {named_file}")

        terminal.write_line("=" * 70)
