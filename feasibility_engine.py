"""
Feasibility Engine - Centralized logic for zone analysis and feasibility determination

This module provides reusable functionality for analyzing regulatory zones and determining
feasibility for wind turbine installations based on airport and MoD zone combinations.

Can be imported by batch_processor.py, report_processor.py, or any other modules that need
zone analysis capabilities.
"""

from typing import List, Dict, Optional, Tuple

# ============================================================================
# LAYER CONFIGURATION - Modular structure for zone layers
# Add new layers here without modifying the feasibility logic
# ============================================================================

LAYER_CONFIG = {
    "airport": {
        "name": "Airport",
        "priority_order": ["funnel", "inner", "middle", "outer"],
        "db_table": "airport_layers",
        "query_fields": ["zone", "name", "type", "radio", "elevation"],
        "special_handlers": None,  # No special handling for airport zones
    },
    "mod": {
        "name": "MoD",
        "priority_order": ["NO_WTG", "NOC", "NO_NOC"],
        "db_table": "mod_layers",
        "query_fields": ["zone", "name", "type"],
        "special_handlers": ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"],  # These override all
    },
    "forest": {
        "name": "Forest",
        "priority_order": ["inner"],
        "db_table": "reserve_forests",
        "query_fields": ["name"],
        "special_handlers": None,
    }
}

# Feasibility determination rules (can be extended for new layers)
# Based on airport zone priority: funnel/inner = No, middle = NOC, outer = Yes
# MoD zones can override to more restrictive (No > NOC > Yes)
FEASIBILITY_RULES = {
    # (airport_zone, mod_zone) -> (feasibility, color)
    # FUNNEL ZONE: Most restrictive - always No unless no other zones
    ("funnel", "NO_WTG"): ("No", "red"),
    ("funnel", "SPECIAL_ALLOWED"): ("No", "red"),
    ("funnel", "SPECIAL_LIMITED_HEIGHT"): ("No", "red"),
    ("funnel", "NOC"): ("No", "red"),
    ("funnel", "NO_NOC"): ("No", "red"),
    ("funnel", None): ("No", "red"),
    # INNER ZONE: Restrictive - always No
    ("inner", "NO_WTG"): ("No", "red"),
    ("inner", "SPECIAL_ALLOWED"): ("No", "red"),
    ("inner", "SPECIAL_LIMITED_HEIGHT"): ("No", "red"),
    ("inner", "NOC"): ("No", "red"),
    ("inner", "NO_NOC"): ("No", "red"),
    ("inner", None): ("No", "red"),
    # MIDDLE ZONE: Moderate - NOC required
    ("middle", "NO_WTG"): ("No", "red"),
    ("middle", "SPECIAL_ALLOWED"): ("NOC", "yellow"),
    ("middle", "SPECIAL_LIMITED_HEIGHT"): ("NOC", "yellow"),
    ("middle", "NOC"): ("NOC", "yellow"),
    ("middle", "NO_NOC"): ("NOC", "yellow"),
    ("middle", None): ("NOC", "yellow"),
    # OUTER ZONE: Least restrictive
    ("outer", "NO_WTG"): ("No", "red"),
    ("outer", "SPECIAL_ALLOWED"): ("Yes", "green"),
    ("outer", "SPECIAL_LIMITED_HEIGHT"): ("Yes", "green"),
    ("outer", "NOC"): ("NOC", "yellow"),
    ("outer", "NO_NOC"): ("Yes", "green"),
    ("outer", None): ("Yes", "green"),
    # NO AIRPORT ZONE - Only MoD evaluation
    (None, "NO_WTG"): ("No", "red"),
    (None, "SPECIAL_ALLOWED"): ("Yes", "green"),
    (None, "SPECIAL_LIMITED_HEIGHT"): ("Yes", "green"),
    (None, "NOC"): ("NOC", "yellow"),
    (None, "NO_NOC"): ("Yes", "green"),
    (None, None): ("Yes", "green"),
}

# ============================================================================
# ZONE ANALYSIS FUNCTIONS - Find most restrictive zones per layer
# ============================================================================

def find_most_restrictive_zone(
    zones: List[Dict],
    layer_key: str
) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Find the most restrictive zone from a list of zones for a given layer.
    
    Uses priority order from LAYER_CONFIG. For MoD layers, special handlers
    (SPECIAL_ALLOWED, SPECIAL_LIMITED_HEIGHT) override all other zones.
    
    Args:
        zones: List of zone dicts from database query
        layer_key: Key in LAYER_CONFIG (e.g., "airport", "mod")
        
    Returns:
        Tuple of (zone_type_string, full_zone_dict)
        - zone_type_string: The zone type that determines feasibility (e.g., "funnel", "NO_WTG")
        - full_zone_dict: Complete zone data including name, type, etc. or None if no zones
    """
    if not zones:
        return None, None
    
    config = LAYER_CONFIG.get(layer_key)
    if not config:
        return None, None
    
    # Check for special handlers first (for MoD zones)
    if config.get("special_handlers"):
        for special_type in config["special_handlers"]:
            for zone in zones:
                if zone.get("zone") == special_type:
                    return special_type, zone
    
    # Find by priority order
    for priority_zone in config["priority_order"]:
        for zone in zones:
            if zone.get("zone") == priority_zone:
                return priority_zone, zone
    
    # No zones found matching priority
    return None, None


def find_most_restrictive_airport_zone(zones: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
    """Wrapper for finding most restrictive airport zone."""
    return find_most_restrictive_zone(zones, "airport")


def find_most_restrictive_mod_zone(zones: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
    """Wrapper for finding most restrictive MoD zone."""
    return find_most_restrictive_zone(zones, "mod")


def find_most_restrictive_forest_zone(zones: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
    """Wrapper for finding most restrictive forest zone."""
    return find_most_restrictive_zone(zones, "forest")


def determine_feasibility(
    airport_zone_type: Optional[str],
    mod_zone_type: Optional[str],
    forest_zone_type: Optional[str] = None
) -> Tuple[str, str]:
    """
    Determine overall feasibility and color based on most restrictive zones.
    
    Uses FEASIBILITY_RULES to map zone combinations to feasibility outcomes.
    
    Args:
        airport_zone_type: Most restrictive airport zone type (e.g., "funnel") or None
        mod_zone_type: Most restrictive MoD zone type (e.g., "NO_WTG") or None
        forest_zone_type: Most restrictive forest zone type (always "inner") or None
        
    Returns:
        Tuple of (feasibility, color)
        - feasibility: "Yes", "NOC", or "No"
        - color: "green", "yellow", or "red"
    """
    if forest_zone_type:
        return ("No", "red")

    key = (airport_zone_type, mod_zone_type)
    
    # Use rule lookup, default to permissive if rule not found
    result = FEASIBILITY_RULES.get(key, ("Yes", "green"))
    return result


def format_zone_description(zone_type: Optional[str], zone_dict: Optional[Dict], layer_key: str) -> str:
    """
    Format a zone as a human-readable string.
    
    Args:
        zone_type: The zone type (e.g., "funnel", "NO_WTG")
        zone_dict: Full zone data from database
        layer_key: Layer key (e.g., "airport", "mod")
        
    Returns:
        Formatted string like "funnel - Indira Gandhi International" or "No zones exist"
    """
    if not zone_type or not zone_dict:
        return "No zones exist"
    
    layer_name = LAYER_CONFIG.get(layer_key, {}).get("name", layer_key.upper())
    zone_name = zone_dict.get("name", "Unknown")
    return f"{zone_type} - {zone_name}"


# ============================================================================
# REPORT-SPECIFIC UTILITY FUNCTIONS
# ============================================================================

def calc_min_height(elev: float, air_elev: float, distance_m: float) -> float:
    """
    Calculate minimum height for WTG based on airport elevation and distance.
    
    Formula: min(air_elev + (45 + 0.05 * (distance_m - 4000)) - elev, 300)
    
    Args:
        elev: Ground elevation at the point (meters)
        air_elev: Airport elevation (meters)
        distance_m: Distance from point to airport (meters)
        
    Returns:
        Minimum height in meters (0 if negative)
    """
    air_elev = float(air_elev)
    mh = min(air_elev + (45 + 0.05 * (distance_m - 4000)) - elev, 300)
    return max(0, mh)


def calculate_autosettle(radio: str, distance_m: float) -> str:
    """
    Determine if auto-settlement is possible based on airport type and distance.
    
    Rules:
    - VFR airports: Auto-settle if > 20km
    - IFR airports: Auto-settle if > 56km
    
    Args:
        radio: Radio type (e.g., "VFR", "IFR")
        distance_m: Distance from point to airport (meters)
        
    Returns:
        "Yes" or "No"
    """
    if radio == "VFR" and distance_m > 20000:
        return "Yes"
    elif "IFR" in radio and distance_m > 56000:
        return "Yes"
    else:
        return "No"


def generate_airport_note(zone_type: str, zone_name: str) -> str:
    """
    Generate detailed note for airport zone based on type.
    
    Args:
        zone_type: Airport zone type (funnel/inner/middle/outer)
        zone_name: Name of the airport
        
    Returns:
        Descriptive note explaining feasibility constraints
    """
    notes = {
        "funnel": f"No WTGs allowed in funnel zone.",
        "inner": f"No WTGs allowed in inner zone.",
        "middle": f"NOC required in middle zone. Based on distance and minimum height.",
        "outer": f"Feasible in outer zone but still require NOC for most cases."
    }
    return notes.get(zone_type, "N/A")


def generate_mod_note(zone_type: str, zone_name: str) -> str:
    """
    Generate detailed note for MoD zone based on type.
    
    Args:
        zone_type: MoD zone type (NO_WTG/NOC/NO_NOC/SPECIAL_*)
        zone_name: Name of the MoD zone
        
    Returns:
        Descriptive note explaining feasibility constraints
    """
    notes = {
        "NO_WTG": f"No WTGs allowed in MoD restricted zone.",
        "NOC": f"NOC required from MoD for this zone.",
        "NO_NOC": f"No NOC required from MoD for this zone.",
        "SPECIAL_ALLOWED": f"WTGs specially allowed in this MoD zone.",
        "SPECIAL_LIMITED_HEIGHT": f"Limited to 83.5m AGL constructions in this special MoD zone."
    }
    return notes.get(zone_type, "N/A")


def generate_combined_note(
    feasibility: str,
    most_restrictive_airport: Optional[Tuple[str, Dict]],
    most_restrictive_mod: Optional[Tuple[str, Dict]],
    most_restrictive_forest: Optional[Tuple[str, Dict]] = None
) -> str:
    """
    Generate comprehensive note for combined feasibility analysis.
    
    Args:
        feasibility: Overall feasibility ("Yes", "NOC", "No")
        most_restrictive_airport: Tuple of (zone_type, zone_dict) or None
        most_restrictive_mod: Tuple of (zone_type, zone_dict) or None
        most_restrictive_forest: Tuple of (zone_type, zone_dict) or None
        
    Returns:
        Detailed note explaining the combined determination
    """
    zones_mentioned = []
    
    if feasibility == "No":
        reasons = []
        if most_restrictive_airport and most_restrictive_airport[0]:
            airport_zone, airport_dict = most_restrictive_airport
            reasons.append(f"Airport {airport_zone} zone at {airport_dict.get('name', 'Unknown')}")
        if most_restrictive_mod and most_restrictive_mod[0]:
            mod_zone, mod_dict = most_restrictive_mod
            if mod_zone == "NO_WTG":
                reasons.append(f"MoD {mod_zone} zone at {mod_dict.get('name', 'Unknown')}")
        if most_restrictive_forest and most_restrictive_forest[0]:
            _, forest_dict = most_restrictive_forest
            reasons.append(f"Forest inner zone at {forest_dict.get('name', 'Unknown Forest')}")
        return f"Not feasible due to: {' and '.join(reasons)}."
    
    elif feasibility == "NOC":
        reasons = []
        if most_restrictive_airport and most_restrictive_airport[0]:
            airport_zone, airport_dict = most_restrictive_airport
            if airport_zone in ["middle", "outer"]:
                reasons.append(f"Airport {airport_zone} zone at {airport_dict.get('name', 'Unknown')}")
        if most_restrictive_mod and most_restrictive_mod[0]:
            mod_zone, mod_dict = most_restrictive_mod
            if mod_zone == "NOC":
                reasons.append(f"MoD {mod_zone} zone ({mod_dict.get('name', 'Unknown')})")
        return f"NOC required due to: {' and '.join(reasons)}."
    
    else:  # Yes
        if most_restrictive_mod and most_restrictive_mod[0]:
            mod_zone, mod_dict = most_restrictive_mod
            zones_mentioned.append(f"MoD {mod_zone} zone ({mod_dict.get('name', 'Unknown')})")

        if most_restrictive_forest and most_restrictive_forest[0]:
            _, forest_dict = most_restrictive_forest
            zones_mentioned.append(f"Forest zone at {forest_dict.get('name', 'Unknown Forest')}")
        
        if most_restrictive_airport and most_restrictive_airport[0]:
            airport_zone, airport_dict = most_restrictive_airport
            zones_mentioned.append(f"Airport {airport_zone} zone at {airport_dict.get('name', 'Unknown')}")
        
        if zones_mentioned:
            return f"Location is feasible. Located in: {' and '.join(zones_mentioned)}."
        else:
            return "Location is feasible."


# ============================================================================
# REPORT BUILDER FUNCTIONS - Build complete zone reports
# ============================================================================

def build_airport_zone_report(
    zone_dict: Dict,
    distance_m: float,
    elev: float
) -> Dict:
    """
    Build complete airport zone report with all required fields.
    
    Args:
        zone_dict: Zone data from database (zone, name, type, radio, elevation, CCZM_Cities)
        distance_m: Distance from point to airport (meters)
        elev: Ground elevation at the point (meters)
        
    Returns:
        Complete report dict with all fields for API response
    """
    zone_type = zone_dict.get("zone")
    name = zone_dict.get("name")
    air_type = zone_dict.get("type")
    radio = zone_dict.get("radio")
    air_elev = float(zone_dict.get("elevation", 0))
    cczm = "na" if zone_dict.get("CCZM_Cities") is None else zone_dict.get("CCZM_Cities")
    
    # Determine feasibility and calculate min_height based on zone type
    if zone_type in ("funnel", "inner"):
        feasibility = "No"
        min_height = "Restricted"
    elif zone_type == "middle":
        feasibility = "NOC"
        mh = calc_min_height(elev, air_elev, distance_m)
        min_height = f"{mh:.1f}m"
    elif zone_type == "outer":
        feasibility = "Yes"
        min_height = "Not Required"
    else:
        feasibility = "N/A"
        min_height = "N/A"
    
    note = generate_airport_note(zone_type, name)
    
    return {
        "layer": "airport",
        "zone": zone_type,
        "name": name,
        "type": air_type,
        "radio": radio,
        "airport_elevation": air_elev,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility,
        "distance": distance_m,
        "cczm": cczm,
        "autoSettle": "N/A"
    }


def build_mod_zone_report(zone_dict: Dict) -> Dict:
    """
    Build complete MoD zone report with all required fields.
    
    Args:
        zone_dict: Zone data from database (zone, name, type)
        
    Returns:
        Complete report dict with all fields for API response
    """
    zone_type = zone_dict.get("zone")
    name = zone_dict.get("name")
    mod_type = zone_dict.get("type")
    
    # Determine feasibility and min_height based on zone type
    if zone_type == "NO_WTG":
        feasibility = "No"
        min_height = "Restricted"
    elif zone_type == "NOC":
        feasibility = "NOC"
        min_height = "Not Applicable"
    elif zone_type == "NO_NOC":
        feasibility = "Yes"
        min_height = "Not Required"
    elif zone_type == "SPECIAL_ALLOWED":
        feasibility = "Yes"
        min_height = "Not Required"
    elif zone_type == "SPECIAL_LIMITED_HEIGHT":
        feasibility = "Yes"
        min_height = "83.5m AGL"
    else:
        feasibility = "N/A"
        min_height = "N/A"
    
    note = generate_mod_note(zone_type, name)
    
    return {
        "layer": "mod",
        "zone": zone_type,
        "name": name,
        "type": mod_type,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility
    }


def build_forest_zone_report(zone_dict: Dict) -> Dict:
    """
    Build complete forest zone report.

    All forest zones are treated as inner/restricted zones.
    """
    name = zone_dict.get("name") or "Unknown Forest"

    return {
        "layer": "forest",
        "zone": "inner",
        "name": name,
        "type": "forest",
        "min_height": "Restricted",
        "note": "No WTGs allowed in forest zone.",
        "feasibility": "No"
    }


def build_combined_analysis(
    airport_reports: List[Dict],
    mod_reports: List[Dict],
    most_restrictive_airport: Optional[Tuple[str, Dict]],
    most_restrictive_mod: Optional[Tuple[str, Dict]],
    elev: float,
    forest_reports: Optional[List[Dict]] = None,
    most_restrictive_forest: Optional[Tuple[str, Dict]] = None
) -> Dict:
    """
    Build combined feasibility analysis report.
    
    Args:
        airport_reports: List of individual airport zone reports
        mod_reports: List of individual MoD zone reports
        most_restrictive_airport: Tuple of (zone_type, zone_dict) or None
        most_restrictive_mod: Tuple of (zone_type, zone_dict) or None
        forest_reports: List of individual forest zone reports
        most_restrictive_forest: Tuple of (zone_type, zone_dict) or None
        elev: Ground elevation at the point (meters)
        
    Returns:
        Combined analysis dict with feasibility, min_height, note, contributing_restrictions
    """
    # Get zone types for feasibility determination
    airport_zone_type = most_restrictive_airport[0] if most_restrictive_airport else None
    mod_zone_type = most_restrictive_mod[0] if most_restrictive_mod else None
    forest_zone_type = most_restrictive_forest[0] if most_restrictive_forest else None
    
    # Determine combined feasibility
    feasibility, color = determine_feasibility(airport_zone_type, mod_zone_type, forest_zone_type)
    
    # Build contributing restrictions list
    contributing_restrictions = []
    if most_restrictive_airport and most_restrictive_airport[0]:
        airport_zone, airport_dict = most_restrictive_airport
        contributing_restrictions.append(
            f"Airport: {airport_zone} zone - {airport_dict.get('name', 'Unknown')}"
        )
    if most_restrictive_mod and most_restrictive_mod[0]:
        mod_zone, mod_dict = most_restrictive_mod
        contributing_restrictions.append(
            f"MoD: {mod_zone} zone - {mod_dict.get('name', 'Unknown')}"
        )
    if most_restrictive_forest and most_restrictive_forest[0]:
        forest_zone, forest_dict = most_restrictive_forest
        contributing_restrictions.append(
            f"Forest: {forest_zone} zone - {forest_dict.get('name', 'Unknown Forest')}"
        )
    
    # Generate comprehensive note
    note = generate_combined_note(
        feasibility,
        most_restrictive_airport,
        most_restrictive_mod,
        most_restrictive_forest
    )
    
    # Aggregate min_height from all zones
    all_reports = airport_reports + mod_reports + (forest_reports or [])
    min_heights = [
        r["min_height"] for r in all_reports 
        if r["min_height"] not in ["N/A", "Not Required", "Not Applicable", "Restricted"]
    ]
    
    if feasibility == "No":
        final_min_height = "Restricted"
    elif min_heights:
        # Extract numeric heights and find maximum
        try:
            numeric_heights = []
            for mh in min_heights:
                if "m" in str(mh):
                    height_val = str(mh).replace("m", "").replace(" AGL", "").strip()
                    numeric_heights.append(float(height_val))
            if numeric_heights:
                final_min_height = f"{max(numeric_heights):.1f}m"
            else:
                final_min_height = min_heights[0]
        except:
            final_min_height = "Not Applicable"
    else:
        final_min_height = "Not Required"
    
    return {
        "layer": "combined",
        "zone": "Combined Analysis",
        "feasibility": feasibility,
        "min_height": final_min_height,
        "note": note,
        "contributing_restrictions": contributing_restrictions,
        "total_airport_zones": len(airport_reports),
        "total_mod_zones": len(mod_reports),
        "total_forest_zones": len(forest_reports or [])
    }
