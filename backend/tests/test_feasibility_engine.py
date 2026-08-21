from app.engine.feasibility_engine import (
    build_combined_analysis,
    build_inner_zone_report,
    determine_feasibility,
    find_most_restrictive_inner_zone,
)


def test_inner_zone_is_more_restrictive_than_other_layers():
    result = determine_feasibility("outer", "NO_NOC", None, "Reservoir")
    assert result == ("No", "red")


def test_no_inner_zone_preserves_existing_feasibility_rules():
    result = determine_feasibility("outer", "NO_NOC", None, None)
    assert result == ("Yes", "green")


def test_find_most_restrictive_inner_zone_uses_category_priority():
    zones = [
        {"category": "Defence Protected Area", "name": "Lower priority"},
        {"category": "Reservoir", "name": "Higher priority"},
    ]

    result = find_most_restrictive_inner_zone(zones)

    assert result == ("Reservoir", {"category": "Reservoir", "name": "Higher priority"})


def test_inner_zone_report_names_category_and_feature():
    report = build_inner_zone_report(
        {"category": "Reservoir", "name": "Nagarjuna Sagar"}
    )
    assert report["layer"] == "inner_zones"
    assert report["zone"] == "Reservoir"
    assert report["name"] == "Nagarjuna Sagar"
    assert report["feasibility"] == "No"


def test_combined_analysis_counts_and_names_inner_zone_restriction():
    combined = build_combined_analysis(
        [], [], None, None, 0, [], None,
        [build_inner_zone_report({"category": "Sanctuary", "name": "Example"})],
        ("Sanctuary", {"category": "Sanctuary", "name": "Example"}),
    )
    assert combined["total_inner_zone_zones"] == 1
    assert "Inner Zones: Sanctuary - Example" in combined["contributing_restrictions"]
