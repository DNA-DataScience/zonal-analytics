import uvicorn
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
from report_processor import generate_report
from sqlalchemy.ext.asyncio import AsyncSession
from connect_db import get_db
from batch_processor import generate_batch_report


# Pydantic models for batch request
class Coordinate(BaseModel):
    id: int
    lat: float
    lon: float

class BatchRequest(BaseModel):
    coordinates: List[Coordinate]


# Import and include routers
from airport_api import router as airport_router
from tiles import router as tiles_router
from points import router as points_router
from analytics_router import router as analytics_router, create_tables

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize analytics tables on startup"""
    db = None
    try:
        from connect_db import AsyncSessionLocal
        db = AsyncSessionLocal()
        await create_tables(db)
    except Exception as e:
        print(f"Failed to create analytics tables: {str(e)}")
    finally:
        if db:
            await db.close()
    yield
    # Shutdown logic here if needed (runs on app shutdown)

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

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

app.include_router(airport_router, prefix="/airport", tags=["airport"])
app.include_router(tiles_router, prefix="/tiles", tags=["tiles"])
app.include_router(points_router, prefix="/points", tags=["points"])
app.include_router(analytics_router)


@app.get("/report-generator")
async def report_generator(lat: float, lng: float, elev: float = 0, db: AsyncSession = Depends(get_db)):
    return await generate_report(lat, lng, elev, db)


@app.post("/batch-generator")
async def batch_generator(request: BatchRequest, db: AsyncSession = Depends(get_db)):
    async with BATCH_SEMAPHORE:
        try:
            coordinates_dict = [coord.model_dump() for coord in request.coordinates]
            result = await generate_batch_report(coordinates_dict, db)
            
            # Stream CSV as download response
            csv_content = result["csv_content"]
            timestamp = result["timestamp"]
            filename = f"batch_{timestamp}.csv"
            
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    
    if os.getenv("ENV") != "dev":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

 
    
