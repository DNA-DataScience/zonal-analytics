import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
import asyncio
from report_processor import generate_report
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from connect_db import get_db


# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
    expose_headers=["*"],
)

# Import and include routers
from airport_api import router as airport_router

app.include_router(airport_router, prefix="/airport", tags=["airport"])

TILE_SEMAPHORE = asyncio.Semaphore(5)

MAX_ZOOM = 15
        
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
    geom3857,
    ST_TileEnvelope(:z, :x, :y),
    4096, 256, true
  ) AS geometry
  FROM "GisDB".airport_layers
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")

@app.get("/tiles/{z}/{x}/{y}.mvt")
async def get_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    
    if z > MAX_ZOOM:
            # return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            return Response(status_code=204)
        
    async with TILE_SEMAPHORE:
        try:    
            result = await db.execute(QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"Tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/report-generator")
async def report_generator(lat: float, lng: float, elev: float = 0, db: AsyncSession = Depends(get_db)):
    return await generate_report(lat, lng, elev, db)

if __name__ == "__main__":
    
    if os.getenv("ENV") != "dev":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

 
    
