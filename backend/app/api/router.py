"""
Main API v1 router — aggregates all sub-routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)

# Additional routers will be included here as phases progress:
# from app.api.v1 import students, teachers, courses, topics, quizzes
# from app.api.v1 import tutor, recommendations, study_plans, analytics
# from app.api.v1 import documents, experiments, knowledge_graph, explainability
