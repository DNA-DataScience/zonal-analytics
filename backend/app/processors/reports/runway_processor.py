from shapely.geometry import Polygon, MultiPolygon, shape
from shapely import wkb
import numpy as np
import logging
from math import degrees, atan2
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


SELECT_QUERY = text("""
                    SELECT geometry, zone, type, radio, elevation, latitude, longitude
                    FROM "GisDB".airport_layers
                    WHERE name = :airport_name
                    """)

UPDATE_QUERY = text("""
                    UPDATE "GisDB".airport_layers
                    SET 
                        geometry = ST_GeomFromWKB(:geom, 4326),
                        geom3857 = ST_Transform(ST_GeomFromWKB(:geom, 4326), 3857)
                    WHERE name = :name AND zone = :zone

                    """)

INSERT_QUERY = text("""
                    INSERT INTO "GisDB".airport_layers 
                    (geometry, geom3857, zone, name, type, radio, elevation, latitude, longitude)
                    VALUES (
                        ST_GeomFromWKB(:geom, 4326),
                        ST_Transform(ST_GeomFromWKB(:geom, 4326), 3857),
                        :zone, :name, :type, :radio, :elevation, :lat, :lon
                    )

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
    logger.debug("Runway centroid computed at %s", centre_coords)

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
    logger.debug("Runway long side index=%d, orientation angle=%.2f degrees", long_side_idx, angle)

    arc_width = 22
    radius = 30
    wedge1 = create_arc_wedge(centre_coords, radius, angle, arc_width)
    wedge2 = create_arc_wedge(centre_coords, radius, (angle + 180) % 360, arc_width)
    funnel_geometry = wedge1.union(wedge2)
    logger.debug("Funnel wedge geometry built (radius=%dkm, arc_width=%d deg)", radius, arc_width)
    return funnel_geometry


async def process_runway_geometry(runway, airport, db:AsyncSession):
    logger.info("Processing runway funnel geometry for airport=%s", airport)

    funnel_geometry = process_funnel(runway)
    
    # # Load environment variables from .env
    # if os.getenv("ENV") != "dev":
    #     load_dotenv("db.env")

    # # Create database connection
    # USER = os.getenv("user")
    # PASSWORD = os.getenv("password")
    # HOST = os.getenv("host")
    # PORT = os.getenv("port")
    # DBNAME = os.getenv("dbname")

    # # Construct the SQLAlchemy connection string
    # DB_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

    # # DB_URL = "postgresql://mapper:password@localhost:5432/gisdb"
    # engine = create_engine(DB_URL)
    
    try:
        result = await db.execute(SELECT_QUERY, {"airport_name": airport})
        results = await result.fetchall()
        logger.debug("Fetched %d existing airport zone rows for airport=%s", len(results), airport)
        updated_geoms = []
        funnel_exists = False
        for row in results:
            geom, zone, t_ype, radio, elevation, lat, lon = row
            shapely_geom = wkb.loads(geom, hex=True)
            updated_geom = shapely_geom

            if (zone == 'funnel'):
                updated_geom = shapely_geom.union(funnel_geometry)
                funnel_exists = True
                logger.debug("Existing funnel zone found for airport=%s; unioning with new funnel geometry", airport)
            else:
                if (zone == 'inner'):
                    funnel_geometry = funnel_geometry.difference(shapely_geom)
                    logger.debug("Subtracted inner zone from funnel geometry for airport=%s", airport)
                else:
                    updated_geom = shapely_geom.difference(funnel_geometry)
                    logger.debug("Subtracted funnel geometry from zone=%s for airport=%s", zone, airport)

            updated_geoms.append({
                'geometry': updated_geom,
                'zone': zone
            })

        for geom in updated_geoms:
            await db.execute(UPDATE_QUERY, {
                "geom": geom['geometry'].wkb,
                "name": airport,
                "zone": geom["zone"]
            })
        logger.debug("Updated %d zone geometries for airport=%s", len(updated_geoms), airport)

        message = "Geometries updated successfully with unionized funnel zone"

        if not funnel_exists:
            await db.execute(INSERT_QUERY, {
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
            logger.debug("Inserted new funnel zone row for airport=%s", airport)

        await db.commit()
        logger.info("%s (airport=%s)", message, airport)

        return True
    except Exception:
        logger.exception("Error processing runway funnel data for airport=%s", airport)
        await db.rollback()
        return False