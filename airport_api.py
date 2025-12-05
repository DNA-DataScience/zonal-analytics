from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from typing import Dict, Any, AsyncGenerator
from runway_processor import process_runway_geometry
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio

# Load environment variables from .env
if os.getenv("ENV") != "dev":
    load_dotenv("db.env")


TILE_SEMAPHORE = asyncio.Semaphore(5)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
    expose_headers=["*"],
)

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construct the SQLAlchemy connection string
DB_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
# DB_URL = "postgresql://mapper:password@localhost:5432/gisdb"

engine = create_async_engine(
    DB_URL,
    pool_size = 10,
    max_overflow = 5,
    pool_timeout = 5,
    pool_recycle = 1800,
    echo = False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# engine = create_engine(DB_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MAX_ZOOM = 15

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        
QUERY = text("""
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

@app.get("/tiles/{z}/{x}/{y}.mvt")
async def get_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    
    if z > MAX_ZOOM:
            # return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            return Response(status_code=204)
        
    async with TILE_SEMAPHORE:
        try:    
            result = await db.execute(QUERY, {"z": z, "x": x, "y": y})
            tile_bytes = result.scalar()
            
            if tile_bytes:
                return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
            else:
                return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
        except Exception as e:
            print(f"Tile error z={z}, x={x}, y={y}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # try:    
    #     result = await db.execute(QUERY, {"z": z, "x": x, "y": y})
    #     tile_bytes = result.scalar()
            
    #     if tile_bytes:
    #         return Response(content=tile_bytes, media_type="application/vnd.mapbox-vector-tile")
    #     else:
    #         return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
            
    # except Exception as e:
    #     print(f"Tile error z={z}, x={x}, y={y}: {e}")
    #     raise HTTPException(status_code=500, detail=str(e))

@app.post("/airport/runway-funnel")
async def update_runway_funnel(runway_data: Dict[Any, Any]):
    try:
        runway = runway_data['features'][0]
        airport = runway_data['airportName']
        success = process_runway_geometry(runway, airport)
        if success:
            return {"status": "success", "message": "Runway funnel data processed and saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process runway funnel data")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
