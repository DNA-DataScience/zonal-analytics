from dotenv import load_dotenv
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio

# Load environment variables from .env
if os.getenv("ENV") != "dev":
    load_dotenv("db.env")
    
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
    pool_size = 5,
    max_overflow = 0,
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
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

