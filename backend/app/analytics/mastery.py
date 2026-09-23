"""
Mastery level classification.

Thresholds are loaded from application Settings so they can be adjusted
via environment variables without code changes.

Mastery levels (ascending):
    not_started → beginner → intermediate → advanced → mastered
"""
from __future__ import annotations

from app.config import get_settings

MASTERY_LEVELS = ["not_started", "beginner", "intermediate", "advanced", "mastered"]


def classify_mastery_level(score: float) -> str:
    """
    Classify a mastery score (0.0–1.0) into a named mastery level.

    Thresholds come from Settings:
        mastery_beginner_threshold     (default 0.35)
        mastery_intermediate_threshold (default 0.65)
        mastery_advanced_threshold     (default 0.85)

    Args:
        score: Mastery score in [0.0, 1.0].

    Returns:
        One of: "not_started" | "beginner" | "intermediate" | "advanced" | "mastered"
    """
    if score <= 0.0:
        return "not_started"

    settings = get_settings()
    if score < settings.mastery_beginner_threshold:
        return "beginner"
    if score < settings.mastery_intermediate_threshold:
        return "intermediate"
    if score < settings.mastery_advanced_threshold:
        return "advanced"
    return "mastered"


def mastery_level_to_score(level: str) -> float:
    """
    Return the approximate midpoint score for a mastery level.
    Useful for seeding new records.
    """
    mapping = {
        "not_started": 0.0,
        "beginner": 0.20,
        "intermediate": 0.50,
        "advanced": 0.75,
        "mastered": 0.92,
    }
    return mapping.get(level, 0.0)


def compute_mastery_score(
    attempts: int,
    correct_count: int,
    recent_accuracy: float,
    average_accuracy: float,
    *,
    recent_weight: float = 0.60,
    average_weight: float = 0.40,
) -> float:
    """
    Compute a mastery score (0.0–1.0) from attempt statistics.

    The score is a weighted blend of recent and average accuracy,
    giving more weight to recent performance (default 60/40 split).
    Returns 0.0 if no attempts have been made.

    Args:
        attempts:         Total quiz/question attempts.
        correct_count:    Total correct answers.
        recent_accuracy:  Accuracy over the last N attempts (0.0–1.0).
        average_accuracy: Overall historical accuracy (0.0–1.0).
        recent_weight:    Weight for recent accuracy (default 0.60).
        average_weight:   Weight for average accuracy (default 0.40).

    Returns:
        Mastery score in [0.0, 1.0].
    """
    if attempts == 0:
        return 0.0

    # Clamp inputs
    recent_accuracy = max(0.0, min(1.0, recent_accuracy))
    average_accuracy = max(0.0, min(1.0, average_accuracy))

    score = recent_weight * recent_accuracy + average_weight * average_accuracy
    return round(max(0.0, min(1.0, score)), 4)


def compute_mastery_confidence(attempts: int, *, max_attempts_for_full_confidence: int = 20) -> float:
    """
    Estimate confidence in the mastery score based on number of attempts.

    Confidence rises from 0.0 toward 1.0 as the student accumulates more
    attempts. Full confidence (1.0) is reached at `max_attempts_for_full_confidence`.

    This is a data-quantity confidence measure — NOT a probability or
    calibrated uncertainty estimate.

    Args:
        attempts:                       Total attempts so far.
        max_attempts_for_full_confidence: Attempt count at which confidence saturates.

    Returns:
        Confidence in [0.0, 1.0].
    """
    if attempts <= 0:
        return 0.0
    confidence = min(1.0, attempts / max_attempts_for_full_confidence)
    return round(confidence, 4)
