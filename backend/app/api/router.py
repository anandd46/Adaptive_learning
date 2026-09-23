"""
Main API v1 router — aggregates all sub-routers.
Phase 1: auth
Phase 2: events, sessions, students, teacher
"""
from fastapi import APIRouter

from app.api.v1 import auth, events, students, teachers, knowledge_gaps

router = APIRouter(prefix="/api/v1")

# ─── Phase 1 ─────────────────────────────────────────────────────────────────
router.include_router(auth.router)

# ─── Phase 2 & 3 — Data, Learning Analytics & Knowledge Gaps ────────────────
router.include_router(events.router)          # /events
router.include_router(events.session_router)  # /sessions
router.include_router(students.router)        # /students/me, /students/me/mastery, etc.
router.include_router(knowledge_gaps.student_router) # /students/me/knowledge-gaps
router.include_router(teachers.router)        # /teacher/dashboard, /teacher/students
router.include_router(knowledge_gaps.teacher_router) # /teacher/students/{id}/knowledge-gaps

# Future phases:
# from app.api.v1 import courses, topics, quizzes
# from app.api.v1 import tutor, recommendations, study_plans, analytics
# from app.api.v1 import documents, experiments, knowledge_graph, explainability
