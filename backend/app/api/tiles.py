from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import  DBAPIError, InterfaceError, OperationalError
import asyncio
import logging
from app.db.connect_db import get_db, reset_db_pool_if_needed
import time

TILE_RETRY_DELAYS_SECONDS = (0.2, 0.5)
TILE_RETRY_BUDGET_SECONDS = 2.0


async def _execute_tile_query(db: AsyncSession, query, params: dict, tile_name: str):
    started = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        try:
            result = await db.execute(query, params)
            return result.scalar()
        except Exception as exc:
            if not _is_transient_db_error(exc):
                raise

            elapsed = time.monotonic() - started
            next_delay = TILE_RETRY_DELAYS_SECONDS[min(attempts - 1, len(TILE_RETRY_DELAYS_SECONDS) - 1)]

            if elapsed + next_delay > TILE_RETRY_BUDGET_SECONDS:
                pool_reset_triggered = await reset_db_pool_if_needed()
                logger.warning(
                    "%s tile degraded after transient DB failures",
                    tile_name,
                    extra={
                        "event": "tile_db_fallback",
                        "attempts": attempts,
                        "elapsed_seconds": round(elapsed, 3),
                        "pool_reset_triggered": pool_reset_triggered,
                        "error": str(exc),
                    },
                )
                raise

            await asyncio.sleep(next_delay)


router = APIRouter()
logger = logging.getLogger(__name__)

TILE_SEMAPHORE = asyncio.Semaphore(3)
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

FOREST_QUERY = text("""
SELECT ST_AsMVT(tile, 'reserve_forests', 4096, 'geometry') as mvt
FROM (
  SELECT
  "Name",
  ST_AsMVTGeom(
    geom3857,
    ST_TileEnvelope(:z, :x, :y),
    4096, 256, true
  ) AS geometry
  FROM "GisDB".reserve_forests
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")

INNER_ZONES_QUERY = text("""
SELECT ST_AsMVT(tile, 'inner_zones', 4096, 'geometry') as mvt
FROM (
  SELECT
  "Name",
  category,
  state_code,
  state_name,
  ST_AsMVTGeom(
    geom3857,
    ST_TileEnvelope(:z, :x, :y),
    4096, 256, true
  ) AS geometry
  FROM "GisDB".inner_zones
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")


@router.get("/airport/{z}/{x}/{y}.mvt")
async def get_airport_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        return Response(status_code=204)
    
    async with TILE_SEMAPHORE:
        try:
            tile_bytes = await _execute_tile_query(db, AIRPORT_QUERY, {"z": z, "x": x, "y": y}, "Airport")
            
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
            tile_bytes = await _execute_tile_query(db, MOD_QUERY, {"z": z, "x": x, "y": y}, "MoD")
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"MoD tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# @router.get("/forest/{z}/{x}/{y}.mvt")
async def get_forest_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        return Response(status_code=204)
    
    async with TILE_SEMAPHORE:
        try:    
            tile_bytes = await _execute_tile_query(db, FOREST_QUERY, {"z": z, "x": x, "y": y}, "Forest")
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"Forest tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# @router.get("/inner-zones/{z}/{x}/{y}.mvt")
async def get_inner_zones_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        return Response(status_code=204)

    async with TILE_SEMAPHORE:
        try:
            tile_bytes = await _execute_tile_query(db, INNER_ZONES_QUERY, {"z": z, "x": x, "y": y}, "Inner Zones")

            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b"", media_type="application/vnd.mapbox-vector-tile")

        except Exception as exc:
            logger.exception("Inner Zones tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(exc))

def _is_transient_db_error(exc: Exception) -> bool:
    if isinstance(exc, (OSError, TimeoutError, OperationalError, InterfaceError, DBAPIError)):
        return True

    error_text = str(exc).lower()
    transient_markers = (
        "connect call failed",
        "connection",
        "timeout",
        "could not connect",
        "server closed",
        "connection reset",
        "temporarily unavailable",
        "max clients reached",
        "too many clients",
    )
    return any(marker in error_text for marker in transient_markers)