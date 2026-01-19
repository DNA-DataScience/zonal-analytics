from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from runway_processor import process_runway_geometry
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import AsyncSession
from connect_db import get_db


# Load environment variables from .env
if os.getenv("ENV") != "dev":
    load_dotenv("db.env")

router = APIRouter()
    
@router.post("/runway-funnel")
async def update_runway_funnel(runway_data: Dict[Any, Any], db: AsyncSession = Depends(get_db)):
    try:
        runway = runway_data['features'][0]
        airport = runway_data['airportName']
        success = await process_runway_geometry(runway, airport, db)
        if success:
            return {"status": "success", "message": "Runway funnel data processed and saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process runway funnel data")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

