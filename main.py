import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from report_processor import generate_report
from sqlalchemy.ext.asyncio import AsyncSession
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
from tiles import router as tiles_router

app.include_router(airport_router, prefix="/airport", tags=["airport"])
app.include_router(tiles_router, prefix="/tiles", tags=["tiles"])


@app.get("/report-generator")
async def report_generator(lat: float, lng: float, elev: float = 0, db: AsyncSession = Depends(get_db)):
    return await generate_report(lat, lng, elev, db)

if __name__ == "__main__":
    
    if os.getenv("ENV") != "dev":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

 
    
