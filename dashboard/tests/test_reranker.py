"""
Tests for the re-ranker (dashboard.services.reranker).

Validates:
  - rerank_matches preserves original_score
  - adjusted_score is computed correctly with known weights
  - Candidates are reordered by adjusted_score
  - Scores are clamped to [0, 100]
"""

from django.test import TestCase

from dashboard.models import SkillWeightSnapshot
from dashboard.services.reranker import rerank_matches
from dashboard.services.skill_weights import record_feedback


class RerankMatchesTests(TestCase):
    """Tests for the rerank_matches function."""

    def setUp(self):
        SkillWeightSnapshot.objects.all().delete()

    def _make_match(self, candidate_id, score, skills):
        return {
            "candidate_id": candidate_id,
            "candidate_name": f"Candidate {candidate_id}",
            "score": score,
            "matched_skills": skills,
            "gaps": [],
            "status": "completed",
        }

    def test_preserves_original_score(self):
        """rerank_matches should add original_score without mutating it."""
        matches = [self._make_match("1", 80, ["python"])]
        result = rerank_matches(matches)
        self.assertEqual(result[0]["original_score"], 80)

    def test_no_weights_means_same_score(self):
        """With no feedback, adjusted_score should equal original_score."""
        matches = [self._make_match("1", 75, ["python", "sql"])]
        result = rerank_matches(matches)
        self.assertEqual(result[0]["adjusted_score"], 75.0)
        self.assertEqual(result[0]["score"], 75)

    def test_good_fit_increases_score(self):
        """After good_fit feedback, adjusted_score should increase."""
        record_feedback("1", 0, "good_fit", ["python"])
        matches = [self._make_match("1", 80, ["python"])]
        result = rerank_matches(matches)
        self.assertGreater(result[0]["adjusted_score"], 80)

    def test_not_a_fit_decreases_score(self):
        """After not_a_fit feedback, adjusted_score should decrease."""
        record_feedback("1", 0, "not_a_fit", ["python"])
        matches = [self._make_match("1", 80, ["python"])]
        result = rerank_matches(matches)
        self.assertLess(result[0]["adjusted_score"], 80)

    def test_reordering_after_feedback(self):
        """Feedback should reorder candidates by adjusted_score."""
        # Initially: A=70, B=80 → B is ranked first
        matches = [
            self._make_match("A", 70, ["python", "sql"]),
            self._make_match("B", 80, ["docker"]),
        ]

        # Boost python and sql heavily (3 rounds → each +0.15)
        for _ in range(3):
            record_feedback("A", 0, "good_fit", ["python", "sql"])

        # Penalize docker (3 rounds → -0.15)
        for _ in range(3):
            record_feedback("B", 0, "not_a_fit", ["docker"])

        result = rerank_matches(matches)
        # A (boosted python+sql) should now rank above B (penalized docker)
        self.assertEqual(result[0]["candidate_id"], "A")
        self.assertEqual(result[1]["candidate_id"], "B")

    def test_score_clamped_at_100(self):
        """adjusted_score should not exceed 100."""
        # Push weight to max (2.0), score=60 → 60*2.0=120 → clamped to 100
        for _ in range(25):
            record_feedback("1", 0, "good_fit", ["python"])
        matches = [self._make_match("1", 60, ["python"])]
        result = rerank_matches(matches)
        self.assertLessEqual(result[0]["adjusted_score"], 100)

    def test_score_clamped_at_0(self):
        """adjusted_score should not go below 0."""
        matches = [self._make_match("1", 0, ["python"])]
        result = rerank_matches(matches)
        self.assertGreaterEqual(result[0]["adjusted_score"], 0)

    def test_empty_skills_uses_default_weight(self):
        """A match with no matched_skills should use weight 1.0 (score unchanged)."""
        matches = [self._make_match("1", 50, [])]
        result = rerank_matches(matches)
        self.assertEqual(result[0]["adjusted_score"], 50.0)
