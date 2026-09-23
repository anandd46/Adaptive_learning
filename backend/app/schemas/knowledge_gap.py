"""
Pydantic v2 schemas for Phase 3 — Knowledge Gap Detection.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeGapResponse(BaseModel):
    """Knowledge Gap record returned from the API."""
    id: uuid.UUID
    student_id: uuid.UUID
    topic_id: uuid.UUID
    topic_title: str | None = None
    gap_score: float = Field(description="0.0 to 1.0 (higher = bigger gap)")
    severity: str = Field(description="low | medium | high | critical")
    priority: int
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    affected_concepts: list[Any] = Field(default_factory=list)
    prerequisite_info: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    detected_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResolveGapRequest(BaseModel):
    """Request body for marking a knowledge gap as manually resolved."""
    pass
