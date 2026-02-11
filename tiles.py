from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from connect_db import get_db


router = APIRouter()

TILE_SEMAPHORE = asyncio.Semaphore(5)
MAX_ZOOM = 15

AIRPORT_QUERY = text("""
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

MOD_QUERY = text("""
SELECT ST_AsMVT(tile, 'mod_layers', 4096, 'geometry') as mvt
FROM (
  SELECT
  zone,
  name,
  type,
  ST_AsMVTGeom(
    geom3857,
    ST_TileEnvelope(:z, :x, :y),
    4096, 256, true
  ) AS geometry
  FROM "GisDB".mod_layers
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")


@router.get("/airport/{z}/{x}/{y}.mvt")
async def get_airport_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        return Response(status_code=204)
    
    async with TILE_SEMAPHORE:
        try:    
            result = await db.execute(AIRPORT_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"Airport tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/mod/{z}/{x}/{y}.mvt")
async def get_mod_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        return Response(status_code=204)
    
    async with TILE_SEMAPHORE:
        try:    
            result = await db.execute(MOD_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"MoD tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
