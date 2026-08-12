"""
Tests for the feedback submission endpoint (POST /dashboard/feedback/).

Validates:
  - POST returns 200 and creates a MatchFeedback row
  - GET returns 405
  - Missing/invalid fields return 400
"""

import json

from django.test import TestCase, Client
from django.urls import reverse

from dashboard.models import MatchFeedback


class SubmitFeedbackViewTests(TestCase):
    """Tests for the submit_feedback view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("dashboard:feedback")
        MatchFeedback.objects.all().delete()

    def test_post_good_fit_returns_200(self):
        """Valid good_fit POST should return 200 with status ok."""
        response = self.client.post(
            self.url,
            data=json.dumps({
                "match_id": "res_001",
                "recruiter_id": 0,
                "feedback": "good_fit",
                "skill_snapshot": ["python", "sql"],
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_post_creates_feedback_row(self):
        """A valid POST should persist a MatchFeedback row."""
        self.client.post(
            self.url,
            data=json.dumps({
                "match_id": "res_002",
                "recruiter_id": 1,
                "feedback": "not_a_fit",
                "skill_snapshot": ["docker"],
            }),
            content_type="application/json",
        )
        self.assertEqual(MatchFeedback.objects.count(), 1)
        fb = MatchFeedback.objects.first()
        self.assertEqual(fb.match_id, "res_002")
        self.assertEqual(fb.feedback, "not_a_fit")

    def test_get_returns_405(self):
        """GET to the feedback endpoint should return 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_missing_match_id_returns_400(self):
        """Missing match_id should return 400."""
        response = self.client.post(
            self.url,
            data=json.dumps({
                "feedback": "good_fit",
                "skill_snapshot": ["python"],
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_feedback_returns_400(self):
        """Invalid feedback value should return 400."""
        response = self.client.post(
            self.url,
            data=json.dumps({
                "match_id": "res_001",
                "feedback": "maybe",
                "skill_snapshot": ["python"],
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_400(self):
        """Malformed JSON should return 400."""
        response = self.client.post(
            self.url,
            data="not json at all",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
