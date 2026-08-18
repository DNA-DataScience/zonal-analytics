import uvicorn
import os
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
from app.logging_config import configure_logging
from app.processors.reports.report_processor import generate_report
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connect_db import get_db
from app.processors.batches.batch_processor import generate_batch_report

configure_logging()
logger = logging.getLogger(__name__)


# Pydantic models for batch request
class Coordinate(BaseModel):
    id: int
    lat: float
    lon: float

class BatchRequest(BaseModel):
    coordinates: List[Coordinate]


# Import and include routers
from app.api.airport import router as airport_router
from app.api.tiles import router as tiles_router
from app.api.points import router as points_router
from app.api.analytics import router as analytics_router, create_tables
from app.api.feedback import router as feedback_router, create_feedback_table

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize app tables on startup"""
    logger.info("Application startup: initializing database tables")
    db = None
    try:
        from app.db.connect_db import AsyncSessionLocal
        db = AsyncSessionLocal()
        await create_tables(db)
        await create_feedback_table(db)
        logger.info("Startup tables verified/created successfully")
    except Exception:
        logger.exception("Failed to create startup tables")
    finally:
        if db:
            await db.close()
            logger.debug("Startup DB session closed")
    yield
    logger.info("Application shutdown")

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
logger.info("FastAPI app instance created")

# Rate limiting for batch processing
BATCH_SEMAPHORE = asyncio.Semaphore(3)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
logger.debug("CORS middleware configured (allow_origins=*)")

app.include_router(airport_router, prefix="/airport", tags=["airport"])
app.include_router(tiles_router, prefix="/tiles", tags=["tiles"])
app.include_router(points_router, prefix="/points", tags=["points"])
app.include_router(analytics_router)
app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
logger.info("Routers registered: airport, tiles, points, analytics, feedback")


@app.get("/report-generator")
async def report_generator(lat: float, lng: float, elev: float = 0, db: AsyncSession = Depends(get_db)):
    logger.info("GET /report-generator lat=%s lng=%s elev=%s", lat, lng, elev)
    started = time.monotonic()
    try:
        result = await generate_report(lat, lng, elev, db)
        logger.info(
            "Report generated for lat=%s lng=%s in %.3fs",
            lat, lng, time.monotonic() - started,
        )
        return result
    except Exception:
        logger.exception("Report generation failed for lat=%s lng=%s elev=%s", lat, lng, elev)
        raise


@app.post("/batch-generator")
async def batch_generator(request: BatchRequest, db: AsyncSession = Depends(get_db)):
    coordinate_count = len(request.coordinates)
    logger.info("POST /batch-generator received %d coordinates", coordinate_count)
    started = time.monotonic()
    async with BATCH_SEMAPHORE:
        logger.debug("Acquired batch semaphore for %d coordinates", coordinate_count)
        try:
            coordinates_dict = [coord.model_dump() for coord in request.coordinates]
            result = await generate_batch_report(coordinates_dict, db)

            # Stream CSV as download response
            csv_content = result["csv_content"]
            timestamp = result["timestamp"]
            filename = f"batch_{timestamp}.csv"

            logger.info(
                "Batch report generated: %d coordinates, filename=%s, elapsed=%.3fs",
                coordinate_count, filename, time.monotonic() - started,
            )

            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except Exception as e:
            logger.exception("Batch generation failed for %d coordinates", coordinate_count)
            raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":

    if os.getenv("ENV") != "dev":
        logger.info("Starting uvicorn server on 0.0.0.0:8000")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        logger.info("ENV=dev detected; skipping uvicorn.run (expected to be started externally)")

