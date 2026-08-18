from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging
from app.db.connect_db import get_db


router = APIRouter()
logger = logging.getLogger(__name__)

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
        logger.debug("Airport tile z=%s exceeds MAX_ZOOM=%s, returning 204", z, MAX_ZOOM)
        return Response(status_code=204)

    logger.debug("Airport tile request z=%s, x=%s, y=%s", z, x, y)
    async with TILE_SEMAPHORE:
        try:
            result = await db.execute(AIRPORT_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()

            if tile_bytes:
                logger.debug("Airport tile z=%s,x=%s,y=%s: %d bytes", z, x, y, len(tile_bytes))
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                logger.debug("Airport tile z=%s,x=%s,y=%s: empty", z, x, y)
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")

        except Exception as e:
            logger.exception("Airport tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/mod/{z}/{x}/{y}.mvt")
async def get_mod_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        logger.debug("MoD tile z=%s exceeds MAX_ZOOM=%s, returning 204", z, MAX_ZOOM)
        return Response(status_code=204)

    logger.debug("MoD tile request z=%s, x=%s, y=%s", z, x, y)
    async with TILE_SEMAPHORE:
        try:
            result = await db.execute(MOD_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()

            if tile_bytes:
                logger.debug("MoD tile z=%s,x=%s,y=%s: %d bytes", z, x, y, len(tile_bytes))
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                logger.debug("MoD tile z=%s,x=%s,y=%s: empty", z, x, y)
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")

        except Exception as e:
            logger.exception("MoD tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/forest/{z}/{x}/{y}.mvt")
async def get_forest_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        logger.debug("Forest tile z=%s exceeds MAX_ZOOM=%s, returning 204", z, MAX_ZOOM)
        return Response(status_code=204)

    logger.debug("Forest tile request z=%s, x=%s, y=%s", z, x, y)
    async with TILE_SEMAPHORE:
        try:
            result = await db.execute(FOREST_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()

            if tile_bytes:
                logger.debug("Forest tile z=%s,x=%s,y=%s: %d bytes", z, x, y, len(tile_bytes))
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                logger.debug("Forest tile z=%s,x=%s,y=%s: empty", z, x, y)
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")

        except Exception as e:
            logger.exception("Forest tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/inner-zones/{z}/{x}/{y}.mvt")
async def get_inner_zones_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    if z > MAX_ZOOM:
        logger.debug("Inner Zones tile z=%s exceeds MAX_ZOOM=%s, returning 204", z, MAX_ZOOM)
        return Response(status_code=204)

    logger.debug("Inner Zones tile request z=%s, x=%s, y=%s", z, x, y)
    async with TILE_SEMAPHORE:
        try:
            result = await db.execute(INNER_ZONES_QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()

            if tile_bytes:
                logger.debug("Inner Zones tile z=%s,x=%s,y=%s: %d bytes", z, x, y, len(tile_bytes))
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                logger.debug("Inner Zones tile z=%s,x=%s,y=%s: empty", z, x, y)
                return Response(content=b"", media_type="application/vnd.mapbox-vector-tile")

        except Exception as exc:
            logger.exception("Inner Zones tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(exc))
