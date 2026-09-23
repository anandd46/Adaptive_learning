"""
Learning Analytics package — Phase 2.
"""
from app.analytics.mastery import (
    classify_mastery_level,
    compute_mastery_confidence,
    compute_mastery_score,
    mastery_level_to_score,
)
from app.analytics.engine import (
    compute_class_statistics,
    compute_engagement_score,
    compute_performance_features,
    update_learner_profile,
    update_student_topic_mastery,
)

__all__ = [
    "classify_mastery_level",
    "compute_mastery_confidence",
    "compute_mastery_score",
    "mastery_level_to_score",
    "compute_class_statistics",
    "compute_engagement_score",
    "compute_performance_features",
    "update_learner_profile",
    "update_student_topic_mastery",
]
