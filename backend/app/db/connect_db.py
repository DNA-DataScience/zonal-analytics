from dotenv import load_dotenv
import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio
import time

logger = logging.getLogger(__name__)

# Load environment variables from .env
if os.getenv("ENV") != "dev":
    logger.info("Loading database credentials from db.env")
    load_dotenv("db.env")
else:
    logger.info("ENV=dev detected; expecting DB credentials from process environment")

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

if not all([USER, HOST, PORT, DBNAME]):
    logger.warning(
        "One or more DB connection env vars are missing (user=%s, host=%s, port=%s, dbname=%s)",
        bool(USER), HOST, PORT, DBNAME,
    )

# Construct the SQLAlchemy connection string
DB_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
# DB_URL = "postgresql://mapper:password@localhost:5432/gisdb"

logger.info("Creating async SQLAlchemy engine for host=%s port=%s db=%s (pool_size=5, max_overflow=5)", HOST, PORT, DBNAME)

engine = create_async_engine(
    DB_URL,
    pool_size = 5,
    max_overflow = 5,
    pool_timeout = 30,
    pool_recycle = 300,
    pool_pre_ping = True,
    echo = False,
    connect_args={
        "timeout": 8,
        "command_timeout": 10,
        "server_settings": {
            "tcp_keepalives_idle": "30",
            "tcp_keepalives_interval": "10",
            "tcp_keepalives_count": "3",
        },
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

_POOL_RESET_LOCK = asyncio.Lock()
_LAST_POOL_RESET_AT = 0.0
_POOL_RESET_COOLDOWN_SECONDS = 30

# engine = create_engine(DB_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a scoped AsyncSession per request, always closing it on exit."""
    async with AsyncSessionLocal() as session:
        logger.debug("DB session opened (id=%s)", id(session))
        try:
            yield session
        finally:
            logger.debug("DB session closed (id=%s)", id(session))


async def reset_db_pool_if_needed() -> bool:
    """Dispose engine pool with cooldown to force fresh connections after transient failures."""
    global _LAST_POOL_RESET_AT

    async with _POOL_RESET_LOCK:
        now = time.time()
        if now - _LAST_POOL_RESET_AT < _POOL_RESET_COOLDOWN_SECONDS:
            logger.debug(
                "Skipping DB pool reset; still within %ss cooldown (%.1fs remaining)",
                _POOL_RESET_COOLDOWN_SECONDS,
                _POOL_RESET_COOLDOWN_SECONDS - (now - _LAST_POOL_RESET_AT),
            )
            return False

        logger.warning("Disposing DB engine pool to force fresh connections after transient failures")
        await engine.dispose()
        _LAST_POOL_RESET_AT = now
        logger.info("DB engine pool disposed and will be recreated on next connection")
        return True

