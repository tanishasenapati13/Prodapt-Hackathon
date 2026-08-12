"""
Tests for the skill weight store (dashboard.services.skill_weights).

Validates:
  - good_fit feedback increments skill weights
  - Weight caps at WEIGHT_MAX (2.0)
  - not_a_fit feedback decrements skill weights
  - Weight floors at WEIGHT_MIN (0.3)
  - Unseen skills default to 1.0
  - record_feedback creates a MatchFeedback row
"""

from django.test import TestCase

from dashboard.models import MatchFeedback, SkillWeightSnapshot
from dashboard.services.skill_weights import (
    get_skill_weight,
    get_all_weights,
    record_feedback,
    WEIGHT_DELTA,
    WEIGHT_MAX,
    WEIGHT_MIN,
)


class SkillWeightTests(TestCase):
    """Tests for skill weight logic."""

    def setUp(self):
        # Ensure clean state
        SkillWeightSnapshot.objects.all().delete()
        MatchFeedback.objects.all().delete()

    def test_unseen_skill_returns_default(self):
        """An unseen skill should return weight 1.0."""
        self.assertEqual(get_skill_weight("unknown_skill"), 1.0)

    def test_good_fit_increments_weight(self):
        """A 'good_fit' feedback should increase skill weights."""
        record_feedback("res_001", 0, "good_fit", ["python", "sql"])
        self.assertAlmostEqual(get_skill_weight("python"), 1.0 + WEIGHT_DELTA)
        self.assertAlmostEqual(get_skill_weight("sql"), 1.0 + WEIGHT_DELTA)

    def test_not_a_fit_decrements_weight(self):
        """A 'not_a_fit' feedback should decrease skill weights."""
        record_feedback("res_001", 0, "not_a_fit", ["python", "sql"])
        self.assertAlmostEqual(get_skill_weight("python"), 1.0 - WEIGHT_DELTA)
        self.assertAlmostEqual(get_skill_weight("sql"), 1.0 - WEIGHT_DELTA)

    def test_weight_caps_at_max(self):
        """Weight should never exceed WEIGHT_MAX."""
        # Apply many good_fit rounds to push weight above max
        rounds = int((WEIGHT_MAX - 1.0) / WEIGHT_DELTA) + 5
        for _ in range(rounds):
            record_feedback("res_001", 0, "good_fit", ["python"])
        self.assertAlmostEqual(get_skill_weight("python"), WEIGHT_MAX)

    def test_weight_floors_at_min(self):
        """Weight should never fall below WEIGHT_MIN."""
        # Apply many not_a_fit rounds to push weight below min
        rounds = int((1.0 - WEIGHT_MIN) / WEIGHT_DELTA) + 5
        for _ in range(rounds):
            record_feedback("res_001", 0, "not_a_fit", ["python"])
        self.assertAlmostEqual(get_skill_weight("python"), WEIGHT_MIN)

    def test_record_feedback_creates_row(self):
        """record_feedback should create a MatchFeedback DB row."""
        record_feedback("res_001", 0, "good_fit", ["python"])
        self.assertEqual(MatchFeedback.objects.count(), 1)
        fb = MatchFeedback.objects.first()
        self.assertEqual(fb.match_id, "res_001")
        self.assertEqual(fb.feedback, "good_fit")
        self.assertEqual(fb.skill_snapshot, ["python"])

    def test_get_all_weights_returns_dict(self):
        """get_all_weights should return a dict with all adjusted skills."""
        record_feedback("res_001", 0, "good_fit", ["python", "sql"])
        weights = get_all_weights()
        self.assertIsInstance(weights, dict)
        self.assertIn("python", weights)
        self.assertIn("sql", weights)

    def test_multiple_feedbacks_accumulate(self):
        """Multiple feedbacks should accumulate weight changes."""
        record_feedback("res_001", 0, "good_fit", ["python"])
        record_feedback("res_002", 0, "good_fit", ["python"])
        expected = 1.0 + 2 * WEIGHT_DELTA
        self.assertAlmostEqual(get_skill_weight("python"), expected)
