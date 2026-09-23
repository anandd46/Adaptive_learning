"""
Pydantic v2 schemas for Phase 2 — Data & Learning Analytics.
Covers: student events, learning sessions, topic mastery, learner profiles,
performance summaries, and teacher dashboard data.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ─── Event Types ──────────────────────────────────────────────────────────────

class EventType(str, Enum):
    """Allowed student event types for the event tracking API."""
    RESOURCE_VIEW        = "resource_view"
    VIDEO_STARTED        = "video_started"
    VIDEO_COMPLETED      = "video_completed"
    QUIZ_STARTED         = "quiz_started"
    QUIZ_COMPLETED       = "quiz_completed"
    HINT_REQUESTED       = "hint_requested"
    TUTOR_MESSAGE        = "tutor_message"
    TOPIC_REVISIT        = "topic_revisit"
    STUDY_PLAN_OPENED    = "study_plan_opened"
    RECOMMENDATION_VIEWED = "recommendation_viewed"
    RECOMMENDATION_ACTED = "recommendation_acted"


# ─── Event Schemas ────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    """Request body for recording a student event."""
    event_type: EventType
    topic_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    """Full event record returned from the API."""
    id: uuid.UUID
    student_id: uuid.UUID
    session_id: uuid.UUID | None
    event_type: str
    topic_id: uuid.UUID | None
    resource_id: uuid.UUID | None
    event_data: dict[str, Any]
    occurred_at: datetime

    model_config = {"from_attributes": True}


# ─── Session Schemas ──────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """Request body for starting a learning session."""
    course_id: uuid.UUID | None = None
    session_type: str = Field(default="study", pattern="^(study|quiz|tutor|review)$")


class SessionUpdate(BaseModel):
    """Request body for ending/updating a session."""
    duration_seconds: int | None = Field(default=None, ge=0)


class SessionResponse(BaseModel):
    """Learning session record."""
    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID | None
    session_type: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int

    model_config = {"from_attributes": True}


# ─── Mastery Schemas ──────────────────────────────────────────────────────────

class TopicMasteryResponse(BaseModel):
    """Per-topic mastery record for a student."""
    topic_id: uuid.UUID
    topic_title: str | None = None       # joined from Topic table
    mastery_score: float
    mastery_level: str
    confidence: float
    attempts: int
    correct_count: int
    recent_accuracy: float
    average_accuracy: float
    last_assessed_at: datetime | None

    model_config = {"from_attributes": True}


# ─── Performance Schemas ──────────────────────────────────────────────────────

class PerformanceFeatures(BaseModel):
    """
    Derived performance features for a student-topic pair.
    These are computed by the analytics engine from raw quiz/event data.

    IMPORTANT: These are descriptive statistics derived from interaction data.
    They are NOT predictions, model outputs, or research-validated metrics.
    """
    recent_accuracy: float = Field(description="Accuracy in last 3 quiz attempts (0.0–1.0)")
    average_accuracy: float = Field(description="Overall historical accuracy (0.0–1.0)")
    accuracy_trend: float = Field(description="Delta accuracy (recent minus earlier). Positive = improving.")
    avg_time_per_question_seconds: float = Field(description="Average seconds spent per question")
    retry_rate: float = Field(description="Fraction of questions attempted more than once")
    hint_usage_rate: float = Field(description="Fraction of questions where a hint was used")
    attempt_count: int = Field(description="Total quiz attempts for this topic")
    total_questions_answered: int = Field(description="Total individual question responses")


class StudentPerformanceSummary(BaseModel):
    """
    Aggregated performance summary across all topics for a student.
    Suitable for display on the student dashboard.
    """
    overall_mastery: float
    topics_started: int
    topics_mastered: int
    total_quiz_attempts: int
    average_accuracy_across_topics: float
    strongest_topic: str | None = None
    weakest_topic: str | None = None
    current_streak_days: int
    engagement_score: float


# ─── Learner Profile Schemas ──────────────────────────────────────────────────

class LearnerProfileResponse(BaseModel):
    """
    Aggregated learner model — reflects state after last analytics run.
    Updated by POST /students/me/profile/refresh.
    """
    student_id: uuid.UUID
    overall_mastery: float
    engagement_score: float
    current_streak_days: int
    weak_topics: list[str]           # list of topic UUIDs
    strong_topics: list[str]         # list of topic UUIDs
    performance_summary: dict[str, Any]
    engagement_metrics: dict[str, Any]
    current_learning_path: list[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Teacher Dashboard Schemas ────────────────────────────────────────────────

class StudentMasterySummary(BaseModel):
    """Per-student summary for the teacher's class overview."""
    student_id: uuid.UUID
    full_name: str
    email: str
    overall_mastery: float
    engagement_score: float
    topics_started: int
    topics_mastered: int
    current_streak_days: int
    at_risk: bool = Field(description="True if overall_mastery < 0.35 or engagement_score < 0.30")


class TeacherDashboardResponse(BaseModel):
    """
    Aggregated class statistics for the teacher dashboard.
    All stats are computed from live DB data.
    """
    total_students: int
    active_students_7d: int          # students with ≥1 event in last 7 days
    average_class_mastery: float
    at_risk_count: int               # students with mastery < 0.35
    topics_with_most_gaps: list[dict[str, Any]]   # [{topic_id, topic_title, gap_count}, ...]
    class_accuracy_by_topic: list[dict[str, Any]] # [{topic_id, title, avg_accuracy}, ...]
