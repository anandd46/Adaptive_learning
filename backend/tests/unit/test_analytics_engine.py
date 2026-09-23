"""
Unit tests for the Learning Analytics Engine (Phase 2).

Tests cover pure computation functions in app.analytics.mastery and app.analytics.engine.
No database required — these are pure Python unit tests.

NOTE: These tests verify that the analytics logic behaves correctly on known
inputs. They do NOT validate research hypotheses or claim educational outcomes.
"""
import pytest

from app.analytics.mastery import (
    classify_mastery_level,
    compute_mastery_confidence,
    compute_mastery_score,
    mastery_level_to_score,
)


# ─── Mastery Score Tests ──────────────────────────────────────────────────────

class TestComputeMasteryScore:
    """Tests for compute_mastery_score()."""

    def test_no_attempts_returns_zero(self):
        score = compute_mastery_score(
            attempts=0, correct_count=0, recent_accuracy=0.0, average_accuracy=0.0
        )
        assert score == 0.0

    def test_perfect_performance(self):
        score = compute_mastery_score(
            attempts=10, correct_count=10, recent_accuracy=1.0, average_accuracy=1.0
        )
        assert score == 1.0

    def test_zero_performance(self):
        score = compute_mastery_score(
            attempts=5, correct_count=0, recent_accuracy=0.0, average_accuracy=0.0
        )
        assert score == 0.0

    def test_recent_weighted_higher_than_average(self):
        """Recent accuracy should have higher weight (0.60) than average (0.40)."""
        # Recent is high, average is low → score should be closer to recent
        score = compute_mastery_score(
            attempts=5, correct_count=3,
            recent_accuracy=0.90,
            average_accuracy=0.30,
        )
        # 0.60 * 0.90 + 0.40 * 0.30 = 0.54 + 0.12 = 0.66
        assert abs(score - 0.66) < 0.01

    def test_output_clamped_to_0_1(self):
        """Output must always be in [0, 1] regardless of inputs."""
        score = compute_mastery_score(
            attempts=5, correct_count=5,
            recent_accuracy=1.5,   # intentionally out of range
            average_accuracy=1.5,
        )
        assert 0.0 <= score <= 1.0

    def test_custom_weights_applied_correctly(self):
        score = compute_mastery_score(
            attempts=4, correct_count=2,
            recent_accuracy=0.80,
            average_accuracy=0.60,
            recent_weight=0.50,
            average_weight=0.50,
        )
        expected = 0.50 * 0.80 + 0.50 * 0.60  # 0.70
        assert abs(score - expected) < 0.01

    def test_returns_float(self):
        score = compute_mastery_score(3, 2, 0.7, 0.6)
        assert isinstance(score, float)


# ─── Mastery Level Classification Tests ──────────────────────────────────────

class TestClassifyMasteryLevel:
    """Tests for classify_mastery_level() using default Settings thresholds."""

    def test_zero_score_is_not_started(self):
        assert classify_mastery_level(0.0) == "not_started"

    def test_negative_score_is_not_started(self):
        assert classify_mastery_level(-0.01) == "not_started"

    def test_low_score_is_beginner(self):
        # Default threshold: beginner < 0.35
        assert classify_mastery_level(0.20) == "beginner"

    def test_at_beginner_threshold_is_intermediate(self):
        # 0.35 is the beginner→intermediate boundary (beginner < 0.35)
        assert classify_mastery_level(0.35) == "intermediate"

    def test_mid_range_is_intermediate(self):
        assert classify_mastery_level(0.50) == "intermediate"

    def test_at_intermediate_threshold_is_advanced(self):
        # 0.65 is the intermediate→advanced boundary
        assert classify_mastery_level(0.65) == "advanced"

    def test_high_score_is_advanced(self):
        assert classify_mastery_level(0.75) == "advanced"

    def test_at_advanced_threshold_is_mastered(self):
        # 0.85 is the advanced→mastered boundary
        assert classify_mastery_level(0.85) == "mastered"

    def test_perfect_score_is_mastered(self):
        assert classify_mastery_level(1.0) == "mastered"

    def test_all_levels_are_valid_strings(self):
        valid = {"not_started", "beginner", "intermediate", "advanced", "mastered"}
        for score in [0.0, 0.1, 0.35, 0.5, 0.65, 0.75, 0.85, 1.0]:
            assert classify_mastery_level(score) in valid


# ─── Mastery Confidence Tests ─────────────────────────────────────────────────

class TestComputeMasteryConfidence:
    """Tests for compute_mastery_confidence()."""

    def test_zero_attempts_gives_zero_confidence(self):
        assert compute_mastery_confidence(0) == 0.0

    def test_negative_attempts_gives_zero(self):
        assert compute_mastery_confidence(-5) == 0.0

    def test_full_confidence_at_max_attempts(self):
        assert compute_mastery_confidence(20) == 1.0

    def test_confidence_exceeds_one_is_clamped(self):
        assert compute_mastery_confidence(100) == 1.0

    def test_half_confidence_at_half_attempts(self):
        conf = compute_mastery_confidence(10, max_attempts_for_full_confidence=20)
        assert abs(conf - 0.50) < 0.01

    def test_confidence_increases_monotonically(self):
        """More attempts → higher confidence."""
        scores = [compute_mastery_confidence(n) for n in range(0, 25)]
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], (
                f"Confidence dropped: {scores[i]} → {scores[i+1]} at attempt {i}"
            )


# ─── Mastery Level to Score Mapping ──────────────────────────────────────────

class TestMasteryLevelToScore:
    """Tests for mastery_level_to_score()."""

    def test_not_started_returns_zero(self):
        assert mastery_level_to_score("not_started") == 0.0

    def test_mastered_returns_high_score(self):
        assert mastery_level_to_score("mastered") >= 0.85

    def test_unknown_level_returns_zero(self):
        assert mastery_level_to_score("nonexistent_level") == 0.0

    def test_all_standard_levels_have_values(self):
        levels = ["not_started", "beginner", "intermediate", "advanced", "mastered"]
        scores = [mastery_level_to_score(lv) for lv in levels]
        # Scores should be in ascending order
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], (
                f"Expected ascending scores: {list(zip(levels, scores))}"
            )
