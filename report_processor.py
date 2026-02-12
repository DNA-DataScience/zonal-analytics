from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
import math

REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation, z."CCZM_Cities",
                           ST_Distance(
                               p.geom4326::geography,
                               z.airport_point::geography
                            ) AS distance_m
                    FROM "GisDB".airport_layers z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);                  
                    """)

NEAREST_QUERY = text("""
                     WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation, z."CCZM_Cities",
                           ST_Distance(
                               p.geom4326::geography,
                               z.airport_point::geography
                            ) AS distance_m
                    FROM "GisDB".airport_layers z
                    CROSS JOIN p
                    ORDER BY
                        z.geom3857 <-> p.geom3857
                    LIMIT 1;    
                     """)

MOD_REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type
                    FROM "GisDB".mod_layers z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);                  
                    """)

async def generate_report(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    
    # Fetch airport zones
    try:
        result = await db.execute(REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        airport_rows = result.fetchall()
    except Exception as e:
        print(f"Error retrieving airport zone data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Fetch MoD zones
    try:
        result = await db.execute(MOD_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        mod_rows = result.fetchall()
    except Exception as e:
        print(f"Error retrieving MoD zone data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    report = []
    
    # Process airport zones
    airport_reports = []
    for r in airport_rows:
        zone = r[0]
        name = r[1]
        air_type = r[2]
        radio = r[3]
        air_elev = r[4]
        distance_m = float(r[6])
        crz = "na" if r[5] is None else r[5]
        
        airport_report = process_airport_zone(zone, name, air_type, radio, air_elev, distance_m, crz, elev)
        airport_reports.append(airport_report)
    
    # If no airport zones found, get nearest airport for auto-settlement info
    nearest_airport_data = None
    if not airport_rows:
        nearest_airport_data = await get_nearest_airport_data(lat, lng, elev, db)
    
    # Process MoD zones
    mod_reports = []
    for r in mod_rows:
        mod_zone = r[0]
        mod_name = r[1]
        mod_type = r[2]
        
        mod_report = process_mod_zone(mod_zone, mod_name, mod_type)
        mod_reports.append(mod_report)
    
    # If we have neither airport zones nor mod zones nor nearest airport, return error
    if not airport_reports and not mod_reports and not nearest_airport_data:
        return JSONResponse(content={"status": "no_results", "message": "No zones or airports found"})
    
    # Create combined analysis first (if we have zone intersections)
    if airport_reports or mod_reports:
        combined = combine_feasibility(airport_reports, mod_reports, elev)
        report.append(combined)
    
    # Add all individual airport zones
    report.extend(airport_reports)
    
    # Add all individual MoD zones
    report.extend(mod_reports)
    
    # Add nearest airport data if no airport zones were found
    if nearest_airport_data:
        report.append(nearest_airport_data)
    
    return JSONResponse(content=report)

def calc_min_height(elev:float, air_elev:float, distance_m:float):
    
    air_elev = float(air_elev)

    mh = min(air_elev + (45 + 0.05 * (distance_m - 4000)) - elev, 300)
    return max(0, mh)

def process_airport_zone(zone: str, name: str, air_type: str, radio: str, air_elev: float, distance_m: float, crz: str, elev: float):
    """Process single airport zone and return report dict"""
    feasibility = "N/A"
    note = "N/A"
    min_height = "N/A"
    autoSettle = "N/A"
    
    if zone in ("funnel", "inner"):
        feasibility = "No"
        note = f"No WTGs allowed in {zone} zone."
        min_height = "Restricted"
    elif zone == "middle":
        feasibility = "NOC"
        note = f"NOC required in middle zone. Based on distance and minimum height."
        mh = calc_min_height(elev, air_elev, distance_m)
        min_height = f"{mh:.1f}m"
    elif zone == "outer":
        feasibility = "Yes"
        note = f"Feasible in outer zone but still require NOC for most cases."
        min_height = "Not Required"
    
    return {
        "layer": "airport",
        "zone": zone,
        "name": name,
        "type": air_type,
        "radio": radio,
        "airport_elevation": air_elev,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility,
        "distance": distance_m,
        "cczm": crz,
        "autoSettle": autoSettle
    }

def process_mod_zone(zone: str, name: str, mod_type: str):
    """Process single MoD zone and return report dict"""
    feasibility = "N/A"
    note = "N/A"
    min_height = "N/A"
    
    if zone == "NO_WTG":
        feasibility = "No"
        note = f"No WTGs allowed in MoD restricted zone."
        min_height = "Restricted"
    elif zone == "NOC":
        feasibility = "NOC"
        note = f"NOC required from MoD for this zone."
        min_height = "Not Applicable"
    elif zone == "NO_NOC":
        feasibility = "Yes"
        note = f"No NOC required from MoD for this zone."
        min_height = "Not Required"
    elif zone == "SPECIAL_ALLOWED":
        feasibility = "Yes"
        note = f"WTGs specially allowed in this MoD zone."
        min_height = "Not Required"
    elif zone == "SPECIAL_LIMITED_HEIGHT":
        feasibility = "Yes"
        note = f"Limited to 83.5m AGL constructions in this special MoD zone."
        min_height = "83.5m AGL"
    
    return {
        "layer": "mod",
        "zone": zone,
        "name": name,
        "type": mod_type,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility
    }

def get_priority_score(report: dict):
    """Get priority score for a report (lower is higher priority)"""
    if report["layer"] == "airport":
        airport_priority = {
            "funnel": 1,
            "inner": 1,
            "middle": 3,
            "outer": 5
        }
        return airport_priority.get(report["zone"], 99)
    else:  # MoD layer
        mod_priority = {
            "SPECIAL_ALLOWED": 0,
            "SPECIAL_LIMITED_HEIGHT": 0,
            "NO_WTG": 2,
            "NOC": 4,
            "NO_NOC": 6
        }
        return mod_priority.get(report["zone"], 99)

def combine_feasibility(airport_reports: list, mod_reports: list, elev: float):
    """Combine airport and MoD reports based on priority with comprehensive note"""
    all_reports = airport_reports + mod_reports
    
    if not all_reports:
        return None
    
    # Collect feasibilities and restrictions
    feasibilities = [r["feasibility"] for r in all_reports]
    contributing_restrictions = []
    
    # Find most restrictive from each layer
    most_restrictive_airport = None
    most_restrictive_mod = None
    
    if airport_reports:
        most_restrictive_airport = min(airport_reports, key=get_priority_score)
    
    if mod_reports:
        # Prioritize SPECIAL zones - they override other MoD zones at the MoD layer
        special_zones = [r for r in mod_reports if r["zone"] in ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"]]
        if special_zones:
            most_restrictive_mod = special_zones[0]  # Use SPECIAL zone as most restrictive
        else:
            most_restrictive_mod = min(mod_reports, key=get_priority_score)
    
    # Determine combined feasibility
    # Step 1: Airport layer takes precedence - if any airport zone says "No", final is "No"
    if most_restrictive_airport and most_restrictive_airport["feasibility"] == "No":
        final_feasibility = "No"
        reasons = [f"Airport {most_restrictive_airport['zone']} zone at {most_restrictive_airport['name']}"]
        contributing_restrictions.append(f"airport: {most_restrictive_airport['zone']} - {most_restrictive_airport['name']}")
        if most_restrictive_mod:
            contributing_restrictions.append(f"mod: {most_restrictive_mod['zone']} - {most_restrictive_mod['name']}")
        final_note = f"Not feasible due to: {' and '.join(reasons)}."
        final_min_height = "Restricted"
        
    # Step 2: Check for SPECIAL zones in MoD layer - they override other MoD zones like NO_WTG
    elif most_restrictive_mod and most_restrictive_mod["zone"] in ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"]:
        final_feasibility = "Yes"  # SPECIAL zones always return "Yes"
        contributing_restrictions.append(f"mod: {most_restrictive_mod['zone']} - {most_restrictive_mod['name']}")
        if most_restrictive_airport:
            contributing_restrictions.append(f"airport: {most_restrictive_airport['zone']} - {most_restrictive_airport['name']}")
        
        zones_mentioned = [f"MoD {most_restrictive_mod['zone']} zone ({most_restrictive_mod['name']})"]
        if most_restrictive_airport:
            zones_mentioned.append(f"Airport {most_restrictive_airport['zone']} zone at {most_restrictive_airport['name']}")
        final_note = f"Location is feasible. Located in: {' and '.join(zones_mentioned)}."
        
        # Preserve height constraint if SPECIAL_LIMITED_HEIGHT
        if most_restrictive_mod["min_height"] != "Not Required":
            final_min_height = most_restrictive_mod["min_height"]
        else:
            final_min_height = "Not Required"
    
    # Step 3: Standard hierarchy - airport "NOC" or other MoD "NOC"
    elif most_restrictive_airport and most_restrictive_airport["feasibility"] == "NOC":
        final_feasibility = "NOC"
        reasons = [f"Airport {most_restrictive_airport['zone']} zone at {most_restrictive_airport['name']}"]
        contributing_restrictions.append(f"airport: {most_restrictive_airport['zone']} - {most_restrictive_airport['name']}")
        if most_restrictive_mod:
            contributing_restrictions.append(f"mod: {most_restrictive_mod['zone']} - {most_restrictive_mod['name']}")
        final_note = f"NOC required due to: {' and '.join(reasons)}."
        
        # Find most restrictive height
        min_heights = [r["min_height"] for r in all_reports if r["min_height"] not in ["N/A", "Not Required", "Not Applicable", "Restricted"]]
        if min_heights:
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
            final_min_height = "Not Applicable"
    
    # Step 4: MoD "NOC" when airport is not "No"
    elif most_restrictive_mod and most_restrictive_mod["feasibility"] == "NOC":
        final_feasibility = "NOC"
        reasons = [f"MoD {most_restrictive_mod['zone']} zone ({most_restrictive_mod['name']})"]
        contributing_restrictions.append(f"mod: {most_restrictive_mod['zone']} - {most_restrictive_mod['name']}")
        if most_restrictive_airport:
            contributing_restrictions.append(f"airport: {most_restrictive_airport['zone']} - {most_restrictive_airport['name']}")
        final_note = f"NOC required due to: {' and '.join(reasons)}."
        
        # Find most restrictive height
        min_heights = [r["min_height"] for r in all_reports if r["min_height"] not in ["N/A", "Not Required", "Not Applicable", "Restricted"]]
        if min_heights:
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
            final_min_height = "Not Applicable"
            
    else:  # All remaining are "Yes"
        final_feasibility = "Yes"
        
        # Build note mentioning the zones
        zones_mentioned = []
        # Add MoD zones first if they exist
        if most_restrictive_mod:
            zones_mentioned.append(f"MoD {most_restrictive_mod['zone']} zone ({most_restrictive_mod['name']})")
            contributing_restrictions.append(f"mod: {most_restrictive_mod['zone']} - {most_restrictive_mod['name']}")
        
        if most_restrictive_airport:
            zones_mentioned.append(f"Airport {most_restrictive_airport['zone']} zone at {most_restrictive_airport['name']}")
            contributing_restrictions.append(f"airport: {most_restrictive_airport['zone']} - {most_restrictive_airport['name']}")
        
        final_note = f"Location is feasible. Located in: {' and '.join(zones_mentioned)}."
        final_min_height = "Not Required"
    
    return {
        "layer": "combined",
        "zone": "Combined Analysis",
        "feasibility": final_feasibility,
        "min_height": final_min_height,
        "note": final_note,
        "contributing_restrictions": contributing_restrictions,
        "total_airport_zones": len(airport_reports),
        "total_mod_zones": len(mod_reports)
    }

async def get_nearest_airport_data(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    """Get nearest airport data for auto-settlement info"""
    try:
        result = await db.execute(NEAREST_QUERY, {
            "lat": lat,
            "lon": lng
        })
        
        row = result.fetchall()
        
        if not row:
            return None
        
    except Exception as e:
        print(f"Error retrieving nearest airport: {str(e)}")
        return None
    
    r = row[0]
    zone = "nearest"
    name = r[1]
    air_type = r[2]
    radio = r[3]
    air_elev = r[4]
    distance_m = float(r[6])
    feasibility = "Feasible"
    note = "Auto Settle only viable if height of WTG is 150m or less"
    min_height = "Not Required"
    crz = "na" if r[5] is None else r[5]
    autoSettle = "No"
    
    if (radio == "VFR" and distance_m > 20000):
        autoSettle = "Yes"
    elif ("IFR" in radio and distance_m > 56000):
        autoSettle = "Yes"
    
    return {
        "layer": "airport",
        "zone": zone,
        "name": name,
        "type": air_type,
        "radio": radio,
        "airport_elevation": air_elev,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility,
        "distance": distance_m,
        "cczm": crz,
        "autoSettle": autoSettle
    }