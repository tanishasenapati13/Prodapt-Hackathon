"""
Tests for dashboard.services.batch_processor.

Validates:
  - Concurrency is bounded by the semaphore
  - Exceptions become graceful error dicts (partial failure doesn't crash the batch)
  - Empty input returns empty output
  - Result ordering matches input ordering
"""

import asyncio
from unittest.mock import AsyncMock, patch
from django.test import TestCase


class BatchProcessorTests(TestCase):
    """Tests for process_resumes_async()."""

    @patch("dashboard.services.batch_processor.get_match_score")
    def test_empty_input_returns_empty(self, mock_score):
        """An empty pairs list should return an empty result list."""
        from dashboard.services.batch_processor import process_resumes_async

        result = asyncio.run(process_resumes_async([]))
        self.assertEqual(result, [])
        mock_score.assert_not_called()

    @patch("dashboard.services.batch_processor.get_match_score")
    def test_all_succeed(self, mock_score):
        """All successful calls should return completed results in order."""
        from dashboard.services.batch_processor import process_resumes_async

        mock_score.side_effect = AsyncMock(
            side_effect=[
                {"score": 90, "matched_skills": ["Python"], "gaps": [], "insight_text": "Great"},
                {"score": 75, "matched_skills": ["Java"], "gaps": ["Docker"], "insight_text": "Good"},
            ]
        )

        pairs = [(1, 10), (2, 10)]
        results = asyncio.run(process_resumes_async(pairs))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["score"], 90)
        self.assertEqual(results[1]["score"], 75)
        self.assertEqual(results[0]["status"], "completed")
        self.assertEqual(results[1]["status"], "completed")

    @patch("dashboard.services.batch_processor.get_match_score")
    def test_partial_failure_graceful(self, mock_score):
        """If one call fails, the others should still return results."""
        from dashboard.services.batch_processor import process_resumes_async

        async def side_effect(resume_id, jd_id):
            if resume_id == 2:
                raise TimeoutError("FastAPI timed out")
            return {"score": 85, "matched_skills": ["Python"], "gaps": [], "insight_text": "OK"}

        mock_score.side_effect = side_effect

        pairs = [(1, 10), (2, 10), (3, 10)]
        results = asyncio.run(process_resumes_async(pairs))

        self.assertEqual(len(results), 3)

        # First and third should succeed
        self.assertEqual(results[0]["status"], "completed")
        self.assertEqual(results[0]["score"], 85)

        # Second should be an error entry, not an exception
        self.assertEqual(results[1]["status"], "error")
        self.assertIn("error", results[1])
        self.assertEqual(results[1]["score"], 0)

        # Third should succeed
        self.assertEqual(results[2]["status"], "completed")

    @patch("dashboard.services.batch_processor.get_match_score")
    def test_concurrency_cap_respected(self, mock_score):
        """
        The semaphore should limit concurrent calls.
        We verify by tracking concurrent execution count.
        """
        from dashboard.services.batch_processor import process_resumes_async

        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_call(resume_id, jd_id):
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            # Simulate work
            await asyncio.sleep(0.05)
            async with lock:
                concurrent_count -= 1
            return {"score": 80, "matched_skills": [], "gaps": [], "insight_text": "OK"}

        mock_score.side_effect = tracked_call

        # 10 pairs with concurrency cap of 3
        pairs = [(i, 1) for i in range(10)]
        results = asyncio.run(process_resumes_async(pairs, concurrency=3))

        self.assertEqual(len(results), 10)
        # Max concurrent should never exceed the semaphore cap
        self.assertLessEqual(max_concurrent, 3)

    @patch("dashboard.services.batch_processor.get_match_score")
    def test_all_fail(self, mock_score):
        """If all calls fail, all results should be error dicts."""
        from dashboard.services.batch_processor import process_resumes_async

        mock_score.side_effect = AsyncMock(
            side_effect=ConnectionError("Service unreachable")
        )

        pairs = [(1, 10), (2, 10)]
        results = asyncio.run(process_resumes_async(pairs))

        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["status"], "error")
            self.assertIn("error", r)
            self.assertEqual(r["score"], 0)
