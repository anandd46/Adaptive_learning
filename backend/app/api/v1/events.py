"""
Event tracking API endpoints — Phase 2.

POST /api/v1/events        — Record a student interaction event
GET  /api/v1/events        — List events for the authenticated student
POST /api/v1/sessions      — Start a learning session
PATCH /api/v1/sessions/{id} — End / update a session
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import pagination_params, require_student
from app.models.models import User
from app.repositories import analytics_repository, student_repository
from app.schemas.analytics import (
    EventCreate,
    EventResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)
from app.schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["Events & Sessions"])

# Session router uses different prefix, included via main router
session_router = APIRouter(prefix="/sessions", tags=["Events & Sessions"])


# ─── Event Endpoints ──────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SuccessResponse[EventResponse],
    status_code=201,
    summary="Record a student event",
    description=(
        "Records a granular learning interaction event (e.g. resource_view, quiz_completed). "
        "Authenticated student only. The event is immediately persisted."
    ),
)
def record_event(
    body: EventCreate,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Record a student interaction event."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    event = analytics_repository.create_event(
        db,
        student_id=student.id,
        event_type=body.event_type.value,
        topic_id=body.topic_id,
        resource_id=body.resource_id,
        session_id=body.session_id,
        event_data=body.event_data,
    )
    db.commit()
    db.refresh(event)

    logger.info(
        "Event recorded",
        extra={"student_id": str(student.id), "event_type": body.event_type.value},
    )
    return {
        "success": True,
        "data": EventResponse.model_validate(event),
        "message": "Event recorded",
    }


@router.get(
    "",
    response_model=PaginatedResponse[EventResponse],
    summary="List events for the authenticated student",
)
def list_events(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[dict, Depends(pagination_params)],
) -> dict:
    """Return paginated events for the current student, newest first."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    total = analytics_repository.count_events(db, student.id)
    events = analytics_repository.list_events(
        db,
        student.id,
        offset=pagination["offset"],
        limit=pagination["page_size"],
    )
    return {
        "success": True,
        "data": [EventResponse.model_validate(e) for e in events],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
        "total_pages": max(1, -(-total // pagination["page_size"])),  # ceil division
    }


# ─── Session Endpoints ────────────────────────────────────────────────────────

@session_router.post(
    "",
    response_model=SuccessResponse[SessionResponse],
    status_code=201,
    summary="Start a learning session",
)
def start_session(
    body: SessionCreate,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create and return a new learning session for the authenticated student."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    session = analytics_repository.create_session(
        db,
        student_id=student.id,
        course_id=body.course_id,
        session_type=body.session_type,
    )
    db.commit()
    db.refresh(session)

    return {
        "success": True,
        "data": SessionResponse.model_validate(session),
        "message": "Session started",
    }


@session_router.patch(
    "/{session_id}",
    response_model=SuccessResponse[SessionResponse],
    summary="End or update a session",
)
def update_session(
    session_id: str,
    body: SessionUpdate,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """End a session and optionally set its duration."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    session = analytics_repository.get_session(db, session_id, student.id)
    if not session:
        raise NotFoundException("Session")

    session = analytics_repository.end_session(db, session, body.duration_seconds)
    db.commit()
    db.refresh(session)

    return {
        "success": True,
        "data": SessionResponse.model_validate(session),
        "message": "Session updated",
    }
