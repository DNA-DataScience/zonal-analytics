import os
import uuid
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from connect_db import get_db, reset_db_pool_if_needed

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

HEARTBEAT_RETRY_BUDGET_SECONDS = 12.0
HEARTBEAT_RETRY_DELAYS_SECONDS = (0.5, 1.0, 2.0, 3.0)


# Pydantic models
class SessionStartRequest(BaseModel):
    anonymous_id: str
    client_env: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None


class HeartbeatRequest(BaseModel):
    session_id: str
    anonymous_id: str


class SessionEndRequest(BaseModel):
    session_id: str
    anonymous_id: str


class EventRequest(BaseModel):
    session_id: str
    event_type: str
    endpoint: Optional[str] = None
    metadata: Optional[dict] = None


class SessionStartResponse(BaseModel):
    session_id: str


def _is_transient_db_error(exc: Exception) -> bool:
    """Detect DB/network failures that are safe to retry for heartbeat writes."""
    if isinstance(exc, (OSError, TimeoutError, OperationalError, InterfaceError, DBAPIError)):
        return True

    error_text = str(exc).lower()
    transient_markers = (
        "connect call failed",
        "connection",
        "timeout",
        "could not connect",
        "server closed",
        "connection reset",
        "temporarily unavailable",
    )
    return any(marker in error_text for marker in transient_markers)


# Helper function to detect if request is from dev environment
def is_dev_request(request: Request) -> bool:
    """Check if request is from dev environment"""
    # Check ENV variable
    if os.getenv("ENV") == "dev":
        return True
    
    # Check if localhost
    client_host = request.client.host if request.client else None
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return True
    
    # Check X-Client-Env header
    client_env_header = request.headers.get("X-Client-Env", "").lower()
    if client_env_header == "development":
        return True
    
    return False


# Database initialization
async def create_tables(db: AsyncSession):
    """Create analytics tables and view if they don't exist"""
    try:
        # Create analytics_sessions table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics_sessions (
                id UUID PRIMARY KEY,
                anonymous_id UUID NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                last_heartbeat_at TIMESTAMPTZ NOT NULL,
                ended_at TIMESTAMPTZ,
                duration_seconds INT,
                is_dev BOOLEAN NOT NULL,
                client_env VARCHAR(20),
                user_agent TEXT,
                referrer TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create analytics_events table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id BIGSERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                endpoint VARCHAR(200),
                occurred_at TIMESTAMPTZ NOT NULL,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create indexes for performance
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_sessions_anonymous_id 
            ON analytics_sessions(anonymous_id);
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_sessions_started_at 
            ON analytics_sessions(started_at);
        """))

        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id 
            ON analytics_events(session_id);
        """))

        # Create view for visitor summary
        await db.execute(text("""
            CREATE OR REPLACE VIEW analytics_visitor_summary AS
            SELECT 
                anonymous_id,
                MIN(started_at) AS first_seen,
                MAX(started_at) AS last_seen,
                COUNT(*) AS total_sessions,
                COALESCE(SUM(duration_seconds), 0) AS total_duration_sec,
                BOOL_OR(is_dev) AS ever_dev
            FROM analytics_sessions
            GROUP BY anonymous_id;
        """))

        await db.commit()
        print("Analytics tables created successfully")
    except Exception as e:
        await db.rollback()
        print(f"Error creating analytics tables: {str(e)}")
        raise


@router.post("/session/start", response_model=SessionStartResponse)
async def session_start(
    request_body: SessionStartRequest, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Start a new analytics session"""
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        is_dev = is_dev_request(request)
        
        # Insert new session
        await db.execute(text("""
            INSERT INTO analytics_sessions 
            (id, anonymous_id, started_at, last_heartbeat_at, is_dev, client_env, user_agent, referrer)
            VALUES (:id, :anonymous_id, :started_at, :last_heartbeat_at, :is_dev, :client_env, :user_agent, :referrer)
        """), {
            "id": session_id,
            "anonymous_id": request_body.anonymous_id,
            "started_at": now,
            "last_heartbeat_at": now,
            "is_dev": is_dev,
            "client_env": request_body.client_env,
            "user_agent": request_body.user_agent,
            "referrer": request_body.referrer,
        })
        
        await db.commit()
        return SessionStartResponse(session_id=session_id)
    except Exception as e:
        await db.rollback()
        raise


@router.post("/heartbeat")
async def heartbeat(
    request_body: HeartbeatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update session heartbeat with transient DB failure tolerance."""
    started = time.monotonic()
    attempts = 0
    now = datetime.utcnow()

    while True:
        attempts += 1
        try:
            await db.execute(text("""
                UPDATE analytics_sessions 
                SET last_heartbeat_at = :now
                WHERE id = :session_id AND anonymous_id = :anonymous_id
            """), {
                "now": now,
                "session_id": request_body.session_id,
                "anonymous_id": request_body.anonymous_id,
            })

            await db.commit()
            return {
                "status": "ok",
                "persisted": True,
                "attempts": attempts,
            }
        except Exception as exc:
            await db.rollback()

            if not _is_transient_db_error(exc):
                raise

            elapsed = time.monotonic() - started
            next_delay = HEARTBEAT_RETRY_DELAYS_SECONDS[min(attempts - 1, len(HEARTBEAT_RETRY_DELAYS_SECONDS) - 1)]
            if elapsed + next_delay > HEARTBEAT_RETRY_BUDGET_SECONDS:
                pool_reset_triggered = await reset_db_pool_if_needed()
                logger.warning(
                    "Heartbeat persisted=false after transient DB failures",
                    extra={
                        "event": "analytics_heartbeat_db_fallback",
                        "attempts": attempts,
                        "elapsed_seconds": round(elapsed, 3),
                        "pool_reset_triggered": pool_reset_triggered,
                        "error": str(exc),
                    },
                )
                return {
                    "status": "ok",
                    "persisted": False,
                    "degraded": True,
                    "attempts": attempts,
                }

            await asyncio.sleep(next_delay)


@router.post("/session/end")
async def session_end(
    request_body: SessionEndRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """End an analytics session"""
    try:
        now = datetime.utcnow()
        
        # Get session to calculate duration
        result = await db.execute(text("""
            SELECT started_at, last_heartbeat_at FROM analytics_sessions
            WHERE id = :session_id AND anonymous_id = :anonymous_id
        """), {
            "session_id": request_body.session_id,
            "anonymous_id": request_body.anonymous_id,
        })
        
        session_row = result.fetchone()
        if not session_row:
            return {"status": "session not found"}
        
        started_at = session_row[0]
        last_heartbeat_at = session_row[1]
        
        # Calculate duration: use actual duration if last heartbeat is later, else estimate from now
        if last_heartbeat_at > started_at:
            duration_seconds = int((last_heartbeat_at - started_at).total_seconds())
        else:
            duration_seconds = int((now - started_at).total_seconds())
        
        # Update session with end time and duration
        await db.execute(text("""
            UPDATE analytics_sessions 
            SET ended_at = :now, duration_seconds = :duration_seconds
            WHERE id = :session_id AND anonymous_id = :anonymous_id
        """), {
            "now": now,
            "duration_seconds": duration_seconds,
            "session_id": request_body.session_id,
            "anonymous_id": request_body.anonymous_id,
        })
        
        await db.commit()
        return {"status": "ok", "duration_seconds": duration_seconds}
    except Exception as e:
        await db.rollback()
        raise


@router.post("/event")
async def event(
    request_body: EventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Log an analytics event"""
    try:
        now = datetime.utcnow()
        import json
        
        # Convert metadata to JSON string
        metadata_json = json.dumps(request_body.metadata) if request_body.metadata else "{}"
        
        # Insert event
        await db.execute(text("""
            INSERT INTO analytics_events 
            (session_id, event_type, endpoint, occurred_at, metadata)
            VALUES (:session_id, :event_type, :endpoint, :occurred_at, :metadata)
        """), {
            "session_id": request_body.session_id,
            "event_type": request_body.event_type,
            "endpoint": request_body.endpoint,
            "occurred_at": now,
            "metadata": metadata_json,
        })
        
        await db.commit()
        return {"status": "ok"}
    except Exception as e:
        await db.rollback()
        raise
