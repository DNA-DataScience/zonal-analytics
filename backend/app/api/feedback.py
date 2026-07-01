import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connect_db import get_db


router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    message: str = Field(..., min_length=1, max_length=2000)


class FeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: str
    created_at: datetime


async def create_feedback_table(db: AsyncSession):
    """Create feedback table in GisDB schema if it does not exist."""
    try:
        await db.execute(text('CREATE SCHEMA IF NOT EXISTS "GisDB";'))
        await db.execute(text('''
            CREATE TABLE IF NOT EXISTS "GisDB".feedback (
                id UUID PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        '''))
        await db.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at
            ON "GisDB".feedback(created_at DESC);
        '''))
        await db.commit()
    except Exception:
        await db.rollback()
        raise


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request_body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Store user feedback from frontend form."""
    feedback_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    try:
        await db.execute(text('''
            INSERT INTO "GisDB".feedback (id, name, message, created_at)
            VALUES (:id, :name, :message, :created_at)
        '''), {
            "id": feedback_id,
            "name": request_body.name,
            "message": request_body.message,
            "created_at": created_at,
        })
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to store feedback")

    return FeedbackResponse(
        status="success",
        message="Feedback submitted",
        feedback_id=feedback_id,
        created_at=created_at,
    )
