from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from app.db.connect_db import get_db


router = APIRouter()
logger = logging.getLogger(__name__)

CMS_QUERY = text("""
SELECT
  "State" AS state,
  "State/ Site Office" AS site_office,
  "Site" AS site,
  ST_AsGeoJSON(geometry)::json AS geom
FROM "GisDB".cms_stations
WHERE geometry IS NOT NULL;
""")

WTG_QUERY = text("""
SELECT
  "CUSTOMER_NAME" AS customer_name,
  "MAIN_SITE" AS main_site,
  "STATE" AS state,
  "INST_CAPACITY" AS inst_capacity,
  "COMM_DATE"::text AS comm_date,
  ST_AsGeoJSON(geometry)::json AS geom
FROM "GisDB".wtg_sites
WHERE geometry IS NOT NULL;
""")


def build_feature_collection(rows, geom_key: str = "geom") -> dict:
    features = [
        {
            "type": "Feature",
            "geometry": row._mapping[geom_key],
            "properties": {k: v for k, v in row._mapping.items() if k != geom_key},
        }
        for row in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get("/cms.geojson")
async def get_cms_points(db: AsyncSession = Depends(get_db)):
    logger.info("GET /points/cms.geojson")
    try:
        result = await db.execute(CMS_QUERY)
        rows = result.fetchall()
        logger.info("CMS points query returned %d rows", len(rows))
        return JSONResponse(content=build_feature_collection(rows))
    except Exception as e:
        logger.exception("CMS points query failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wtg.geojson")
async def get_wtg_points(db: AsyncSession = Depends(get_db)):
    logger.info("GET /points/wtg.geojson")
    try:
        result = await db.execute(WTG_QUERY)
        rows = result.fetchall()
        logger.info("WTG points query returned %d rows", len(rows))
        return JSONResponse(content=build_feature_collection(rows))
    except Exception as e:
        logger.exception("WTG points query failed")
        raise HTTPException(status_code=500, detail=str(e))
