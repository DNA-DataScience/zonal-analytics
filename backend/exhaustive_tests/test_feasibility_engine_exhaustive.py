"""
Exhaustive tests for app/engine/feasibility_engine.py

Covers every public function in the module:
  - find_most_restrictive_zone (+ the 4 layer-specific wrappers)
  - determine_feasibility (every entry in FEASIBILITY_RULES, plus overrides
    and the "unmapped key" default)
  - format_zone_description
  - calc_min_height
  - calculate_autosettle (including boundary conditions and a documented
    edge case)
  - generate_airport_note / generate_mod_note / generate_combined_note
  - build_airport_zone_report / build_mod_zone_report /
    build_forest_zone_report / build_inner_zone_report
  - build_combined_analysis (min-height aggregation, restriction ordering,
    zone counts)

Where the source code has a real behavioral quirk (e.g. calculate_autosettle
blowing up on radio=None), the test documents the current behavior rather
than silently assuming it away, so a future fix is a visible, intentional
change rather than a silent regression.
"""
import time

import pytest

from app.engine.feasibility_engine import (
    LAYER_CONFIG,
    FEASIBILITY_RULES,
    find_most_restrictive_zone,
    find_most_restrictive_airport_zone,
    find_most_restrictive_mod_zone,
    find_most_restrictive_forest_zone,
    find_most_restrictive_inner_zone,
    determine_feasibility,
    format_zone_description,
    calc_min_height,
    calculate_autosettle,
    generate_airport_note,
    generate_mod_note,
    generate_combined_note,
    build_airport_zone_report,
    build_mod_zone_report,
    build_forest_zone_report,
    build_inner_zone_report,
    build_combined_analysis,
)


# ============================================================================
# LAYER_CONFIG sanity
# ============================================================================

class TestLayerConfig:
    @pytest.mark.parametrize("layer_key", ["airport", "mod", "forest", "inner_zones"])
    def test_every_layer_has_required_keys(self, layer_key):
        config = LAYER_CONFIG[layer_key]
        assert "name" in config
        assert "priority_order" in config
        assert "db_table" in config
        assert "query_fields" in config
        assert isinstance(config["priority_order"], list) and config["priority_order"]

    def test_only_mod_layer_declares_special_handlers(self):
        assert LAYER_CONFIG["mod"]["special_handlers"] == ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"]
        assert LAYER_CONFIG["airport"]["special_handlers"] is None
        assert LAYER_CONFIG["forest"]["special_handlers"] is None
        assert LAYER_CONFIG["inner_zones"]["special_handlers"] is None


# ============================================================================
# find_most_restrictive_zone
# ============================================================================

class TestFindMostRestrictiveZone:
    def test_empty_zone_list_returns_none_none(self):
        assert find_most_restrictive_zone([], "airport") == (None, None)

    def test_unknown_layer_key_returns_none_none(self):
        zones = [{"zone": "funnel", "name": "X"}]
        assert find_most_restrictive_zone(zones, "not_a_real_layer") == (None, None)

    def test_no_matching_priority_returns_none_none(self):
        zones = [{"zone": "totally_unrecognized_zone_type", "name": "X"}]
        assert find_most_restrictive_zone(zones, "airport") == (None, None)

    @pytest.mark.parametrize(
        "present_order,expected",
        [
            (["outer", "middle"], "middle"),
            (["outer", "funnel"], "funnel"),
            (["middle", "inner"], "inner"),
            (["outer", "middle", "inner", "funnel"], "funnel"),
            (["outer"], "outer"),
        ],
    )
    def test_airport_priority_order_picks_most_restrictive(self, present_order, expected):
        zones = [{"zone": z, "name": f"airport-{z}"} for z in present_order]
        zone_type, zone_dict = find_most_restrictive_airport_zone(zones)
        assert zone_type == expected
        assert zone_dict["zone"] == expected

    def test_duplicate_zone_types_returns_first_match_in_list_order(self):
        zones = [
            {"zone": "middle", "name": "first-middle"},
            {"zone": "middle", "name": "second-middle"},
        ]
        zone_type, zone_dict = find_most_restrictive_airport_zone(zones)
        assert zone_type == "middle"
        assert zone_dict["name"] == "first-middle"

    @pytest.mark.parametrize("special", ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"])
    def test_mod_special_handler_overrides_priority_order(self, special):
        # NO_WTG is highest normal priority, but special handlers are checked first
        zones = [
            {"zone": "NO_WTG", "name": "restricted-zone"},
            {"zone": special, "name": "special-zone"},
        ]
        zone_type, zone_dict = find_most_restrictive_mod_zone(zones)
        assert zone_type == special
        assert zone_dict["name"] == "special-zone"

    def test_mod_special_allowed_checked_before_special_limited_height(self):
        # special_handlers = ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"]
        zones = [
            {"zone": "SPECIAL_LIMITED_HEIGHT", "name": "limited"},
            {"zone": "SPECIAL_ALLOWED", "name": "allowed"},
        ]
        zone_type, zone_dict = find_most_restrictive_mod_zone(zones)
        assert zone_type == "SPECIAL_ALLOWED"
        assert zone_dict["name"] == "allowed"

    def test_mod_priority_order_without_special_handlers(self):
        zones = [{"zone": "NO_NOC", "name": "a"}, {"zone": "NOC", "name": "b"}]
        zone_type, zone_dict = find_most_restrictive_mod_zone(zones)
        assert zone_type == "NOC"

    def test_forest_layer_only_recognizes_inner(self):
        zones = [{"zone": "inner", "name": "Reserve Forest A"}]
        zone_type, zone_dict = find_most_restrictive_forest_zone(zones)
        assert zone_type == "inner"
        assert zone_dict["name"] == "Reserve Forest A"

    def test_inner_zones_layer_reads_category_field_not_zone_field(self):
        # inner_zones query_fields = ["name", "category", "state_code", "state_name"]
        # "zone" is NOT in query_fields, so extraction falls through to "category"
        zones = [{"category": "Reservoir", "name": "Nagarjuna Sagar"}]
        zone_type, zone_dict = find_most_restrictive_inner_zone(zones)
        assert zone_type == "Reservoir"

    def test_inner_zones_priority_order_among_categories(self):
        zones = [
            {"category": "Defence Protected Area", "name": "lower-priority"},
            {"category": "Coastal Regulatory Zone", "name": "higher-priority"},
        ]
        zone_type, zone_dict = find_most_restrictive_inner_zone(zones)
        assert zone_type == "Coastal Regulatory Zone"
        assert zone_dict["name"] == "higher-priority"

    def test_get_zone_value_fallback_branch_when_field_not_in_query_fields(self, monkeypatch):
        """
        Exercises the final fallback line:
            return zone.get("zone") or zone.get("category")
        which only runs when neither "zone" nor "category" is declared in the
        layer's query_fields (not true for any of the built-in layers, so we
        monkeypatch a minimal custom layer to reach it).
        """
        custom_config = {
            "custom": {
                "name": "Custom",
                "priority_order": ["restricted"],
                "db_table": "custom_layers",
                "query_fields": ["name"],  # neither "zone" nor "category" present
                "special_handlers": None,
            }
        }
        monkeypatch.setattr(
            "app.engine.feasibility_engine.LAYER_CONFIG",
            custom_config,
        )
        zones = [{"zone": "restricted", "name": "fallback-zone"}]
        zone_type, zone_dict = find_most_restrictive_zone(zones, "custom")
        assert zone_type == "restricted"


# ============================================================================
# determine_feasibility - exhaustively walk every rule in FEASIBILITY_RULES
# ============================================================================

class TestDetermineFeasibility:
    @pytest.mark.parametrize("key,expected", list(FEASIBILITY_RULES.items()))
    def test_every_declared_rule_matches_lookup_table(self, key, expected):
        airport_zone_type, mod_zone_type = key
        result = determine_feasibility(airport_zone_type, mod_zone_type)
        assert result == expected

    def test_unmapped_combination_defaults_to_yes_green(self):
        result = determine_feasibility("unknown_airport_zone", "unknown_mod_zone")
        assert result == ("Yes", "green")

    def test_inner_zone_overrides_every_other_input(self):
        # Even a fully "Yes" airport/mod combo is overridden to No when an
        # inner-zone restriction is present.
        result = determine_feasibility("outer", "NO_NOC", None, "Reservoir")
        assert result == ("No", "red")

    def test_forest_zone_overrides_airport_and_mod(self):
        result = determine_feasibility("outer", "NO_NOC", "inner", None)
        assert result == ("No", "red")

    def test_inner_zone_checked_before_forest_zone(self):
        # Both set -> inner branch returns first; forest is never consulted.
        result = determine_feasibility("outer", "NO_NOC", "inner", "Sanctuary")
        assert result == ("No", "red")

    def test_no_restrictions_at_all_defaults_permissive(self):
        assert determine_feasibility(None, None, None, None) == ("Yes", "green")


# ============================================================================
# format_zone_description
# ============================================================================

class TestFormatZoneDescription:
    def test_none_zone_type_returns_no_zones_exist(self):
        assert format_zone_description(None, {"name": "X"}, "airport") == "No zones exist"

    def test_none_zone_dict_returns_no_zones_exist(self):
        assert format_zone_description("funnel", None, "airport") == "No zones exist"

    def test_both_none_returns_no_zones_exist(self):
        assert format_zone_description(None, None, "airport") == "No zones exist"

    def test_formats_known_layer_with_name(self):
        result = format_zone_description("funnel", {"name": "IGI Airport"}, "airport")
        assert result == "funnel - IGI Airport"

    def test_empty_dict_zone_dict_is_falsy_and_returns_no_zones_exist(self):
        # {} is falsy in Python, so `not zone_dict` short-circuits to the
        # "no zones exist" branch even though a zone_type was supplied.
        result = format_zone_description("NOC", {}, "mod")
        assert result == "No zones exist"

    def test_missing_name_key_on_nonempty_dict_defaults_to_unknown(self):
        result = format_zone_description("NOC", {"other_field": "x"}, "mod")
        assert result == "NOC - Unknown"

    def test_unknown_layer_key_still_formats_using_zone_type_and_name(self):
        # layer_name lookup falls back to layer_key.upper(), but that value
        # isn't actually used in the returned string, so this should still work.
        result = format_zone_description("X", {"name": "Y"}, "no_such_layer")
        assert result == "X - Y"


# ============================================================================
# calc_min_height
# ============================================================================

class TestCalcMinHeight:
    def test_matches_documented_formula(self):
        # min(air_elev + (45 + 0.05*(distance_m - 4000)) - elev, 300)
        elev, air_elev, distance_m = 100.0, 150.0, 10000.0
        expected = min(150.0 + (45 + 0.05 * (10000 - 4000)) - 100.0, 300)
        assert calc_min_height(elev, air_elev, distance_m) == expected

    def test_negative_result_is_clamped_to_zero(self):
        # Very high ground elevation relative to airport should floor at 0
        result = calc_min_height(elev=5000, air_elev=100, distance_m=4000)
        assert result == 0

    def test_result_is_capped_at_300(self):
        result = calc_min_height(elev=0, air_elev=0, distance_m=1_000_000)
        assert result == 300

    def test_air_elev_accepts_numeric_string(self):
        result = calc_min_height(elev=0, air_elev="100", distance_m=4000)
        assert result == 145.0

    def test_distance_exactly_4000_uses_base_45m_margin(self):
        result = calc_min_height(elev=0, air_elev=0, distance_m=4000)
        assert result == 45.0


# ============================================================================
# calculate_autosettle
# ============================================================================

class TestCalculateAutosettle:
    def test_vfr_just_above_threshold_is_yes(self):
        assert calculate_autosettle("VFR", 20000.1) == "Yes"

    def test_vfr_exactly_at_threshold_is_no(self):
        # condition is strictly "> 20000"
        assert calculate_autosettle("VFR", 20000) == "No"

    def test_vfr_below_threshold_is_no(self):
        assert calculate_autosettle("VFR", 19999) == "No"

    def test_ifr_just_above_threshold_is_yes(self):
        assert calculate_autosettle("IFR", 56000.1) == "Yes"

    def test_ifr_exactly_at_threshold_is_no(self):
        assert calculate_autosettle("IFR", 56000) == "No"

    def test_ifr_below_threshold_is_no(self):
        assert calculate_autosettle("IFR", 55999) == "No"

    def test_radio_substring_match_for_ifr_variants(self):
        # "IFR" in radio uses substring matching, not equality
        assert calculate_autosettle("IFR/VFR", 56001) == "Yes"

    def test_unrecognized_radio_type_is_no_regardless_of_distance(self):
        assert calculate_autosettle("UNKNOWN", 1_000_000) == "No"

    def test_radio_none_raises_typeerror(self):
        """
        Documents current behavior: calculate_autosettle does not guard
        against radio=None. "VFR" == None is False, so it falls through to
        `"IFR" in radio`, which raises TypeError for a None radio. Callers
        must ensure `radio` is always a string.
        """
        with pytest.raises(TypeError):
            calculate_autosettle(None, 100000)


# ============================================================================
# generate_airport_note / generate_mod_note
# ============================================================================

class TestGenerateNotes:
    @pytest.mark.parametrize(
        "zone_type,expected_snippet",
        [
            ("funnel", "No WTGs allowed in funnel zone"),
            ("inner", "No WTGs allowed in inner zone"),
            ("middle", "NOC required in middle zone"),
            ("outer", "Feasible in outer zone"),
        ],
    )
    def test_generate_airport_note_known_types(self, zone_type, expected_snippet):
        note = generate_airport_note(zone_type, "Some Airport")
        assert expected_snippet in note

    def test_generate_airport_note_unknown_type_returns_na(self):
        assert generate_airport_note("not_a_zone", "X") == "N/A"

    @pytest.mark.parametrize(
        "zone_type,expected_snippet",
        [
            ("NO_WTG", "No WTGs allowed in MoD restricted zone"),
            ("NOC", "NOC required from MoD"),
            ("NO_NOC", "No NOC required from MoD"),
            ("SPECIAL_ALLOWED", "specially allowed"),
            ("SPECIAL_LIMITED_HEIGHT", "83.5m AGL"),
        ],
    )
    def test_generate_mod_note_known_types(self, zone_type, expected_snippet):
        note = generate_mod_note(zone_type, "Some MoD Zone")
        assert expected_snippet in note

    def test_generate_mod_note_unknown_type_returns_na(self):
        assert generate_mod_note("not_a_zone", "X") == "N/A"


# ============================================================================
# generate_combined_note
# ============================================================================

class TestGenerateCombinedNote:
    def test_no_feasibility_lists_all_active_reasons(self):
        note = generate_combined_note(
            "No",
            most_restrictive_airport=("funnel", {"name": "Airport A"}),
            most_restrictive_mod=("NO_WTG", {"name": "Zone B"}),
            most_restrictive_forest=("inner", {"name": "Forest C"}),
            most_restrictive_inner_zone=("Reservoir", {"name": "Reservoir D"}),
        )
        assert note.startswith("Not feasible due to:")
        assert "Inner Zones Reservoir at Reservoir D" in note
        assert "Airport funnel zone at Airport A" in note
        assert "MoD NO_WTG zone at Zone B" in note
        assert "Forest inner zone at Forest C" in note

    def test_no_feasibility_mod_reason_only_included_when_mod_is_no_wtg(self):
        # airport funnel alone is enough to cause "No"; mod=NOC should NOT
        # be listed as a reason since only NO_WTG independently forces "No".
        note = generate_combined_note(
            "No",
            most_restrictive_airport=("funnel", {"name": "Airport A"}),
            most_restrictive_mod=("NOC", {"name": "Zone B"}),
        )
        assert "Airport funnel zone at Airport A" in note
        assert "MoD" not in note

    def test_no_feasibility_single_reason_has_no_and_conjunction(self):
        note = generate_combined_note(
            "No",
            most_restrictive_airport=("inner", {"name": "Only Reason"}),
            most_restrictive_mod=None,
        )
        assert note == "Not feasible due to: Airport inner zone at Only Reason."
        assert " and " not in note

    def test_noc_feasibility_lists_middle_or_outer_airport_and_mod_noc(self):
        note = generate_combined_note(
            "NOC",
            most_restrictive_airport=("middle", {"name": "Airport M"}),
            most_restrictive_mod=("NOC", {"name": "Zone N"}),
        )
        assert note.startswith("NOC required due to:")
        assert "Airport middle zone at Airport M" in note
        assert "MoD NOC zone (Zone N)" in note

    def test_noc_feasibility_ignores_funnel_or_inner_airport_zone(self):
        # NOC branch only mentions airport when zone is "middle" or "outer"
        note = generate_combined_note(
            "NOC",
            most_restrictive_airport=("funnel", {"name": "Should Not Appear"}),
            most_restrictive_mod=("NOC", {"name": "Zone N"}),
        )
        assert "Should Not Appear" not in note

    def test_yes_feasibility_with_no_zones_mentioned(self):
        assert generate_combined_note("Yes", None, None) == "Location is feasible."

    def test_yes_feasibility_lists_mod_then_forest_then_airport(self):
        note = generate_combined_note(
            "Yes",
            most_restrictive_airport=("outer", {"name": "Airport O"}),
            most_restrictive_mod=("NO_NOC", {"name": "Zone Y"}),
            most_restrictive_forest=("inner", {"name": "Forest Z"}),
        )
        mod_idx = note.index("MoD NO_NOC")
        forest_idx = note.index("Forest zone at Forest Z")
        airport_idx = note.index("Airport outer zone at Airport O")
        assert mod_idx < forest_idx < airport_idx


# ============================================================================
# build_airport_zone_report
# ============================================================================

class TestBuildAirportZoneReport:
    def test_funnel_zone_is_not_feasible_restricted(self):
        zone = {"zone": "funnel", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100}
        report = build_airport_zone_report(zone, distance_m=1000, elev=50)
        assert report["feasibility"] == "No"
        assert report["min_height"] == "Restricted"
        assert report["layer"] == "airport"

    def test_inner_zone_is_not_feasible_restricted(self):
        zone = {"zone": "inner", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100}
        report = build_airport_zone_report(zone, distance_m=1000, elev=50)
        assert report["feasibility"] == "No"
        assert report["min_height"] == "Restricted"

    def test_middle_zone_computes_min_height_via_formula(self):
        zone = {"zone": "middle", "name": "A", "type": "civil", "radio": "VFR", "elevation": 150}
        report = build_airport_zone_report(zone, distance_m=10000, elev=100)
        expected = min(150.0 + (45 + 0.05 * (10000 - 4000)) - 100.0, 300)
        assert report["feasibility"] == "NOC"
        assert report["min_height"] == f"{expected:.1f}m"

    def test_outer_zone_is_feasible_no_height_required(self):
        zone = {"zone": "outer", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100}
        report = build_airport_zone_report(zone, distance_m=25000, elev=50)
        assert report["feasibility"] == "Yes"
        assert report["min_height"] == "Not Required"

    def test_unknown_zone_type_is_na(self):
        zone = {"zone": "totally_new", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100}
        report = build_airport_zone_report(zone, distance_m=1000, elev=50)
        assert report["feasibility"] == "N/A"
        assert report["min_height"] == "N/A"

    def test_cczm_none_defaults_to_na_string(self):
        zone = {"zone": "outer", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100, "CCZM_Cities": None}
        report = build_airport_zone_report(zone, distance_m=1000, elev=50)
        assert report["cczm"] == "na"

    def test_cczm_value_is_passed_through(self):
        zone = {"zone": "outer", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100, "CCZM_Cities": "Mumbai"}
        report = build_airport_zone_report(zone, distance_m=1000, elev=50)
        assert report["cczm"] == "Mumbai"

    def test_distance_and_autosettle_field_defaults(self):
        zone = {"zone": "outer", "name": "A", "type": "civil", "radio": "VFR", "elevation": 100}
        report = build_airport_zone_report(zone, distance_m=1234.5, elev=50)
        assert report["distance"] == 1234.5
        assert report["autoSettle"] == "N/A"  # always N/A on this builder


# ============================================================================
# build_mod_zone_report
# ============================================================================

class TestBuildModZoneReport:
    @pytest.mark.parametrize(
        "zone_type,expected_feasibility,expected_min_height",
        [
            ("NO_WTG", "No", "Restricted"),
            ("NOC", "NOC", "Not Applicable"),
            ("NO_NOC", "Yes", "Not Required"),
            ("SPECIAL_ALLOWED", "Yes", "Not Required"),
            ("SPECIAL_LIMITED_HEIGHT", "Yes", "83.5m AGL"),
            ("something_else", "N/A", "N/A"),
        ],
    )
    def test_all_mod_zone_types(self, zone_type, expected_feasibility, expected_min_height):
        zone = {"zone": zone_type, "name": "Zone X", "type": "restricted"}
        report = build_mod_zone_report(zone)
        assert report["layer"] == "mod"
        assert report["feasibility"] == expected_feasibility
        assert report["min_height"] == expected_min_height
        assert report["name"] == "Zone X"


# ============================================================================
# build_forest_zone_report / build_inner_zone_report
# ============================================================================

class TestBuildForestZoneReport:
    def test_named_forest(self):
        report = build_forest_zone_report({"name": "Reserve A"})
        assert report == {
            "layer": "forest",
            "zone": "inner",
            "name": "Reserve A",
            "type": "forest",
            "min_height": "Restricted",
            "note": "No WTGs allowed in forest zone.",
            "feasibility": "No",
        }

    def test_missing_name_defaults_to_unknown_forest(self):
        report = build_forest_zone_report({})
        assert report["name"] == "Unknown Forest"

    def test_empty_string_name_also_defaults_to_unknown_forest(self):
        # `zone_dict.get("name") or "Unknown Forest"` treats "" as falsy too
        report = build_forest_zone_report({"name": ""})
        assert report["name"] == "Unknown Forest"


class TestBuildInnerZoneReport:
    def test_named_inner_zone(self):
        report = build_inner_zone_report({"category": "Sanctuary", "name": "Reserve B"})
        assert report["layer"] == "inner_zones"
        assert report["zone"] == "Sanctuary"
        assert report["name"] == "Reserve B"
        assert report["feasibility"] == "No"

    def test_missing_name_defaults_to_unknown_inner_zone(self):
        report = build_inner_zone_report({"category": "Heritage"})
        assert report["name"] == "Unknown Inner Zone"

    def test_missing_category_key_raises_keyerror(self):
        """
        build_inner_zone_report indexes zone_dict["category"] directly
        (not .get), so a row without that key is a hard failure rather than
        a soft default. This documents that requirement explicitly.
        """
        with pytest.raises(KeyError):
            build_inner_zone_report({"name": "No Category Provided"})


# ============================================================================
# build_combined_analysis
# ============================================================================

class TestBuildCombinedAnalysis:
    def test_no_inputs_at_all_is_feasible_with_zero_counts(self):
        combined = build_combined_analysis([], [], None, None, elev=0)
        assert combined["layer"] == "combined"
        assert combined["feasibility"] == "Yes"
        assert combined["min_height"] == "Not Required"
        assert combined["total_airport_zones"] == 0
        assert combined["total_mod_zones"] == 0
        assert combined["total_forest_zones"] == 0
        # inner-zone args both None/omitted -> key should be absent entirely
        assert "total_inner_zone_zones" not in combined

    def test_total_inner_zone_zones_present_when_reports_list_supplied(self):
        combined = build_combined_analysis(
            [], [], None, None, elev=0, inner_zone_reports=[]
        )
        assert combined["total_inner_zone_zones"] == 0

    def test_total_inner_zone_zones_present_when_tuple_supplied_even_if_reports_none(self):
        combined = build_combined_analysis(
            [], [], None, None, elev=0,
            most_restrictive_inner_zone=(None, None),
        )
        assert combined["total_inner_zone_zones"] == 0

    def test_restricted_feasibility_forces_min_height_restricted(self):
        airport_reports = [{"min_height": "45.0m"}]
        combined = build_combined_analysis(
            airport_reports, [], ("funnel", {"name": "A"}), None, elev=0
        )
        assert combined["feasibility"] == "No"
        assert combined["min_height"] == "Restricted"

    def test_min_height_takes_max_of_numeric_values_with_m_suffix(self):
        airport_reports = [{"min_height": "45.0m"}]
        mod_reports = [{"min_height": "83.5m AGL"}]
        combined = build_combined_analysis(
            airport_reports, mod_reports,
            ("middle", {"name": "A"}), ("SPECIAL_LIMITED_HEIGHT", {"name": "B"}),
            elev=0,
        )
        assert combined["feasibility"] == "NOC"
        assert combined["min_height"] == "83.5m"

    def test_min_height_falls_back_to_first_value_when_none_are_numeric(self):
        # A min_height without "m" in it (and not one of the filtered
        # sentinel strings) skips numeric extraction entirely.
        airport_reports = [{"min_height": "Unquantified"}]
        combined = build_combined_analysis(
            airport_reports, [], ("middle", {"name": "A"}), None, elev=0
        )
        assert combined["min_height"] == "Unquantified"

    def test_min_height_bad_numeric_string_falls_back_to_not_applicable(self):
        # "abcm" contains "m" so it enters numeric_heights parsing, but
        # float("abc") raises -> caught by the bare except -> "Not Applicable"
        airport_reports = [{"min_height": "abcm"}]
        combined = build_combined_analysis(
            airport_reports, [], ("middle", {"name": "A"}), None, elev=0
        )
        assert combined["min_height"] == "Not Applicable"

    def test_min_height_not_required_when_no_heights_and_feasible(self):
        combined = build_combined_analysis(
            [], [], None, ("NO_NOC", {"name": "A"}), elev=0
        )
        assert combined["feasibility"] == "Yes"
        assert combined["min_height"] == "Not Required"

    def test_contributing_restrictions_ordering_inner_airport_mod_forest(self):
        combined = build_combined_analysis(
            [], [],
            ("funnel", {"name": "Airport A"}),
            ("NO_WTG", {"name": "Mod B"}),
            elev=0,
            forest_reports=[],
            most_restrictive_forest=("inner", {"name": "Forest C"}),
            inner_zone_reports=[],
            most_restrictive_inner_zone=("Reservoir", {"name": "Inner D"}),
        )
        restrictions = combined["contributing_restrictions"]
        assert restrictions == [
            "Inner Zones: Reservoir - Inner D",
            "Airport: funnel zone - Airport A",
            "MoD: NO_WTG zone - Mod B",
            "Forest: inner zone - Forest C",
        ]

    def test_zone_counts_reflect_report_list_lengths(self):
        airport_reports = [{"min_height": "N/A"}, {"min_height": "N/A"}]
        mod_reports = [{"min_height": "N/A"}]
        forest_reports = [{"min_height": "N/A"}, {"min_height": "N/A"}, {"min_height": "N/A"}]
        combined = build_combined_analysis(
            airport_reports, mod_reports, None, None, elev=0,
            forest_reports=forest_reports,
        )
        assert combined["total_airport_zones"] == 2
        assert combined["total_mod_zones"] == 1
        assert combined["total_forest_zones"] == 3

    def test_note_field_matches_generate_combined_note_output(self):
        combined = build_combined_analysis(
            [], [], ("outer", {"name": "Airport A"}), ("NO_NOC", {"name": "Mod B"}), elev=0,
        )
        expected_note = generate_combined_note(
            "Yes", ("outer", {"name": "Airport A"}), ("NO_NOC", {"name": "Mod B"})
        )
        assert combined["note"] == expected_note


# ============================================================================
# Response-time tracking for the feasibility engine's hot path
# ============================================================================

class TestFeasibilityEngineResponseTime:
    """
    determine_feasibility and find_most_restrictive_zone sit on the hot path
    for both the single-point report generator and the 100-point batch
    processor, so they're called far more often than any other function in
    this module. This measures and records their per-call latency.
    """

    def test_determine_feasibility_average_call_latency(self, record_timing):
        iterations = 20_000
        start = time.perf_counter()
        for _ in range(iterations):
            determine_feasibility("middle", "NOC", None, None)
        elapsed = time.perf_counter() - start

        avg_us = (elapsed / iterations) * 1_000_000
        record_timing("determine_feasibility", avg_us, "us/call")
        # Pure dict-lookup logic; generous ceiling to avoid sandbox flakiness
        # while still catching a genuine performance regression (e.g. an
        # accidental O(n) scan replacing the O(1) dict lookup).
        assert avg_us < 50

    def test_find_most_restrictive_zone_average_call_latency(self, record_timing):
        zones = [{"zone": z, "name": f"zone-{z}"} for z in ["outer", "middle", "inner", "funnel"]]
        iterations = 20_000
        start = time.perf_counter()
        for _ in range(iterations):
            find_most_restrictive_airport_zone(zones)
        elapsed = time.perf_counter() - start

        avg_us = (elapsed / iterations) * 1_000_000
        record_timing("find_most_restrictive_airport_zone", avg_us, "us/call")
        assert avg_us < 100

    def test_build_combined_analysis_with_large_zone_lists(self, record_timing):
        # Simulate a location that intersects many overlapping zones (a
        # dense urban / multi-jurisdiction area) to check aggregation cost
        # doesn't blow up.
        airport_reports = [{"min_height": f"{i}.0m"} for i in range(500)]
        mod_reports = [{"min_height": "N/A"} for _ in range(500)]

        start = time.perf_counter()
        combined = build_combined_analysis(
            airport_reports, mod_reports,
            ("middle", {"name": "A"}), ("NOC", {"name": "B"}),
            elev=0,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        record_timing("build_combined_analysis[1000 reports]", elapsed_ms, "ms")
        assert combined["total_airport_zones"] == 500
        assert elapsed_ms < 200
