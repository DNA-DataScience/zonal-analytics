from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, Any
from runway_processor import process_runway_geometry
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
    expose_headers=["*"],
)

DB_URL = "postgresql://mapper:password@localhost:5432/gisdb"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MAX_ZOOM = 15

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
QUERY = text("""
SELECT ST_AsMVT(tile, 'airport_layers', 4096, 'geometry') as mvt
FROM (
  SELECT
  zone,
  name,
  type,
  radio,
  elevation,
  latitude,
  longitude,
  ST_AsMVTGeom(
    ST_Transform(geometry, 3857),
    ST_TileEnvelope(:z, :x, :y),
    4096, 256, true
  ) AS geometry
  FROM airport_layers
  WHERE ST_Intersects(
      geometry, 
      ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326)
  )
) AS tile;
""")

@app.get("/tiles/{z}/{x}/{y}.mvt")
async def get_tile(z: int, x: int, y: int, db: Session = Depends(get_db)):
    try:
        if z > MAX_ZOOM:
            return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
        
        result = db.execute(QUERY, {"z": z, "x": x, "y": y})
        tile_bytes = result.scalar()
        
        if tile_bytes:
            return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
        else:
            return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/airport/runway-funnel")
async def update_runway_funnel(runway_data: Dict[Any, Any]):
    try:
        runway = runway_data['features'][0]
        airport = runway_data['airportName']
        success = process_runway_geometry(runway, airport)
        if success:
            return {"status": "success", "message": "Runway funnel data processed and saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process runway funnel data")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
