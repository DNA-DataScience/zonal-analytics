from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from connect_db import get_db


router = APIRouter()

TILE_SEMAPHORE = asyncio.Semaphore(5)
MAX_ZOOM = 15

CMS_QUERY = text("""
SELECT ST_AsMVT(tile, 'cms_stations', 4096, 'geometry') as mvt
FROM (
  SELECT
  "State" as state,
  "State/ Site Office" as site_office,
  "Site" as site,
  ST_AsMVTGeom(
	geom3857,
	ST_TileEnvelope(:z, :x, :y),
	4096, 256, true
  ) AS geometry
  FROM "GisDB".cms_stations
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")

WTG_QUERY = text("""
SELECT ST_AsMVT(tile, 'wtg_sites', 4096, 'geometry') as mvt
FROM (
  SELECT
  "CUSTOMER_NAME" as customer_name,
  "MAIN_SITE" as main_site,
  "STATE" as state,
  "INST_CAPACITY" as inst_capacity,
  ST_AsMVTGeom(
	geom3857,
	ST_TileEnvelope(:z, :x, :y),
	4096, 256, true
  ) AS geometry
  FROM "GisDB".wtg_sites
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")


@router.get("/cms/{z}/{x}/{y}.mvt")
async def get_cms_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
	if z > MAX_ZOOM:
		return Response(status_code=204)

	async with TILE_SEMAPHORE:
		try:
			result = await db.execute(CMS_QUERY, {"z": z, "x": x, "y": y})
			tile_bytes = result.scalar()

			if tile_bytes:
				return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
			return Response(content=b"", media_type="application/vnd.mapbox-vector-tile")

		except Exception as e:
			print(f"CMS tile error z={z}, x={x}, y={y}: {e}")
			raise HTTPException(status_code=500, detail=str(e))


@router.get("/wtg/{z}/{x}/{y}.mvt")
async def get_wtg_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
	if z > MAX_ZOOM:
		return Response(status_code=204)

	async with TILE_SEMAPHORE:
		try:
			result = await db.execute(WTG_QUERY, {"z": z, "x": x, "y": y})
			tile_bytes = result.scalar()

			if tile_bytes:
				return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
			return Response(content=b"", media_type="application/vnd.mapbox-vector-tile")

		except Exception as e:
			print(f"WTG tile error z={z}, x={x}, y={y}: {e}")
			raise HTTPException(status_code=500, detail=str(e))
