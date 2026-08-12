"""
Tests for dashboard views.

Validates:
  - /dashboard/ returns 200 with expected context data
  - /dashboard/candidate/<id>/ returns 200 with candidate detail
  - /dashboard/candidate/<bad_id>/ returns 404
  - Context contains all required chart data
"""

from django.test import TestCase, Client
from django.urls import reverse


class DashboardResultsViewTests(TestCase):
    """Tests for the dashboard_results view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("dashboard:results")

    def test_returns_200(self):
        """Dashboard results page should return 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """Should render the results.html template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "dashboard/results.html")

    def test_context_has_candidates(self):
        """Context should contain a 'candidates' list."""
        response = self.client.get(self.url)
        self.assertIn("candidates", response.context)
        self.assertIsInstance(response.context["candidates"], list)
        self.assertGreater(len(response.context["candidates"]), 0)

    def test_context_has_aggregate_stats(self):
        """Context should contain aggregate statistics."""
        response = self.client.get(self.url)
        ctx = response.context
        self.assertIn("total_candidates", ctx)
        self.assertIn("completed_count", ctx)
        self.assertIn("error_count", ctx)
        self.assertIn("avg_score", ctx)
        self.assertIn("top_score", ctx)

    def test_context_has_chart_data(self):
        """Context should contain Chart.js data arrays."""
        response = self.client.get(self.url)
        ctx = response.context
        self.assertIn("chart_names", ctx)
        self.assertIn("chart_scores", ctx)
        self.assertIn("skill_labels", ctx)
        self.assertIn("skill_counts", ctx)
        # Chart data should be lists
        self.assertIsInstance(ctx["chart_names"], list)
        self.assertIsInstance(ctx["chart_scores"], list)

    def test_candidates_sorted_by_score(self):
        """Candidates should be sorted by score descending."""
        response = self.client.get(self.url)
        candidates = response.context["candidates"]
        scores = [c["score"] for c in candidates]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_page_contains_candidate_name(self):
        """The page HTML should contain at least one candidate name."""
        response = self.client.get(self.url)
        # Rahul Sharma is the top scorer in mock data
        self.assertContains(response, "Rahul Sharma")

    def test_page_contains_chart_canvas(self):
        """The page should have the Chart.js canvas elements."""
        response = self.client.get(self.url)
        self.assertContains(response, 'id="scoresChart"')
        self.assertContains(response, 'id="skillsChart"')


class CandidateDetailViewTests(TestCase):
    """Tests for the candidate_detail view."""

    def setUp(self):
        self.client = Client()

    def test_valid_candidate_returns_200(self):
        """A valid candidate ID should return 200."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """Should render the candidate_detail.html template."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "dashboard/candidate_detail.html")

    def test_context_has_candidate(self):
        """Context should contain the candidate detail dict."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertIn("candidate", response.context)
        self.assertIsNotNone(response.context["candidate"])

    def test_context_has_chart_data(self):
        """Context should contain radar/gap chart data."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        ctx = response.context
        self.assertIn("skill_names", ctx)
        self.assertIn("skill_levels", ctx)
        self.assertIn("gap_names", ctx)
        self.assertIn("gap_importances", ctx)

    def test_invalid_candidate_returns_404(self):
        """A non-existent candidate ID should return 404."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_9999"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_page_contains_candidate_name(self):
        """The detail page should show the candidate's name."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertContains(response, "Rahul Sharma")

    def test_page_contains_insight_text(self):
        """The detail page should display the AI insight."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertContains(response, "Candidate matches 4 of 5")

    def test_page_contains_chart_canvases(self):
        """The page should have the Chart.js canvas elements."""
        url = reverse("dashboard:candidate_detail", kwargs={"candidate_id": "res_001"})
        response = self.client.get(url)
        self.assertContains(response, 'id="radarChart"')
        self.assertContains(response, 'id="gapChart"')
