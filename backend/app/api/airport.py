from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from app.processors.reports.runway_processor import process_runway_geometry
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connect_db import get_db

logger = logging.getLogger(__name__)

# Load environment variables from .env
if os.getenv("ENV") != "dev":
    load_dotenv("db.env")

router = APIRouter()

@router.post("/runway-funnel")
async def update_runway_funnel(runway_data: Dict[Any, Any], db: AsyncSession = Depends(get_db)):
    airport = runway_data.get('airportName', 'unknown')
    logger.info("POST /airport/runway-funnel airport=%s", airport)
    try:
        runway = runway_data['features'][0]
        airport = runway_data['airportName']
        success = await process_runway_geometry(runway, airport, db)
        if success:
            logger.info("Runway funnel data processed and saved for airport=%s", airport)
            return {"status": "success", "message": "Runway funnel data processed and saved"}
        else:
            logger.error("process_runway_geometry returned failure for airport=%s", airport)
            raise HTTPException(status_code=500, detail="Failed to process runway funnel data")

    except HTTPException:
        raise
    except (KeyError, IndexError):
        logger.exception("Malformed runway_data payload for airport=%s", airport)
        raise HTTPException(status_code=400, detail="Invalid runway data payload")
    except Exception as e:
        logger.exception("Unexpected error processing runway funnel for airport=%s", airport)
        raise HTTPException(status_code=500, detail=str(e))

