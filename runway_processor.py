from shapely.geometry import Polygon, MultiPolygon, shape
from shapely import wkb
import numpy as np
from math import degrees, atan2
from sqlalchemy import create_engine, text

SELECT_QUERY = text("""
                    SELECT geometry, zone, type, radio, elevation, latitude, longitude
                    FROM airport_layers
                    WHERE name = :airport_name
                    """)

UPDATE_QUERY = text("""
                    UPDATE airport_layers
                    SET geometry = ST_GeomFromWKB(:geom, 4326)
                    WHERE name = :name and zone = :zone
                    """)

INSERT_QUERY = text("""
                    INSERT INTO airport_layers (geometry, zone, name, type, radio, elevation, latitude, longitude)
                    VALUES (ST_GeomFromWKB(:geom, 4326), :zone, :name, :type, :radio, :elevation, :lat, :lon)
                    """)
            

def create_arc_wedge(center_point, radius_km, start_angle, arc_width, steps=100):
    """Create an arc wedge geometry"""
    radius_deg = radius_km / 111.12  # Convert km to degrees
    angles = np.linspace(start_angle - arc_width/2, start_angle + arc_width/2, steps)
    points = []
    
    # Add center point first
    points.append(center_point)
    
    # Create arc points
    for angle in angles:
        dx = radius_deg * np.cos(np.radians(angle))
        dy = radius_deg * np.sin(np.radians(angle))
        points.append((center_point[0] + dx, center_point[1] + dy))
    
    # Close the polygon by adding center point again
    points.append(center_point)
    
    return Polygon(points)

def process_funnel(runway):
    """Process runway funnel data and update the database"""
    runway_polygon = shape(runway['geometry'])
    runway_centre = runway_polygon.centroid
    centre_coords = (runway_centre.x, runway_centre.y)
    
    corners = list(runway_polygon.exterior.coords)[:-1]
    corners_arr = np.array(corners)
    
    distances = []
    for i in range(4):
        next_i = (i + 1) % 4
        dist = np.sqrt(np.sum((corners_arr[next_i] - corners_arr[i])**2))
        distances.append((dist, i))
        
    distances.sort(reverse=True)
    long_side_idx = distances[0][1]
    
    p1 = corners_arr[long_side_idx]
    p2 = corners_arr[(long_side_idx + 1) % 4]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = degrees(atan2(dy, dx))
    
    arc_width = 22
    radius = 30
    wedge1 = create_arc_wedge(centre_coords, radius, angle, arc_width)
    wedge2 = create_arc_wedge(centre_coords, radius, (angle + 180) % 360, arc_width)
    funnel_geometry = wedge1.union(wedge2)
    return funnel_geometry


def process_runway_geometry(runway, airport):
    
    funnel_geometry = process_funnel(runway)
    
        # Create database connection
    DB_URL = "postgresql://mapper:password@localhost:5432/gisdb"
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as connection:
            results = connection.execute(SELECT_QUERY, {"airport_name": airport}).fetchall()
            updated_geoms = []
            funnel_exists = False
            for row in results:
                geom, zone, t_ype, radio, elevation, lat, lon = row
                shapely_geom = wkb.loads(geom, hex=True)
                
                if (zone == 'funnel'):
                    updated_geom = shapely_geom.union(funnel_geometry)
                    funnel_exists = True
                else:
                    updated_geom = shapely_geom.difference(funnel_geometry)
                    
                print(updated_geom)
                
                updated_geoms.append({
                    'geometry': updated_geom,
                    'zone': zone
                })
                
            
            for geom in updated_geoms:
                connection.execute(UPDATE_QUERY, {
                    "geom": geom['geometry'].wkb,
                    "name": airport,
                    "zone": geom["zone"]
                })
                
            message = "Geometries updated successfully with unionized funnel zone"
            
            if (funnel_exists == False):    
                connection.execute(INSERT_QUERY, {
                    "geom": funnel_geometry.wkb,
                    "zone": 'funnel',
                    "name": airport,
                    "type": t_ype,
                    "radio": radio,
                    "elevation": elevation,
                    "lat": lat,
                    "lon": lon
                })
                message = "Geometries updated successfully with inserted funnel zone"
            
            connection.commit()
            print(message)
        
        return True
    except Exception as e:
        print(f"Error processing runway funnel data: {str(e)}")
        return False

if __name__ == "__main__":
    process_runway_geometry()