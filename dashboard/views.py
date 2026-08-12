"""
Dashboard views — thin controllers that delegate to services/.

Views:
  dashboard_results  — ranked candidate list with chart data
  candidate_detail   — full gap analysis for a single candidate
"""

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services.mock_data import (
    get_mock_candidates,
    get_mock_candidate_detail,
)
from .services.reranker import rerank_matches
from .services.skill_weights import record_feedback

logger = logging.getLogger("dashboard")

# ---------------------------------------------------------------------------
# Toggle: set USE_MOCK = False once Person 2/3 are ready for real integration
# ---------------------------------------------------------------------------
USE_MOCK = True


def dashboard_results(request):
    """
    Display ranked candidate list with aggregate score visualizations.

    GET /dashboard/
    """
    try:
        if USE_MOCK:
            candidates = get_mock_candidates()
        else:
            # TODO: Replace with real DB reads + fastapi_client calls
            # from .services.batch_processor import process_resumes_async
            # from asgiref.sync import async_to_sync
            # candidates = async_to_sync(process_resumes_async)(pairs)
            candidates = get_mock_candidates()

        # Apply feedback-based re-ranking
        candidates = rerank_matches(candidates)

        # Compute aggregate stats for the dashboard header
        total = len(candidates)
        completed = [c for c in candidates if c.get("status") != "error"]
        errors = [c for c in candidates if c.get("status") == "error"]
        avg_score = (
            round(sum(c["score"] for c in completed) / len(completed), 1)
            if completed
            else 0
        )
        top_score = max((c["score"] for c in completed), default=0)

        # Collect all skills across candidates for aggregate chart
        all_skills = {}
        for c in completed:
            for skill in c.get("matched_skills", []):
                all_skills[skill] = all_skills.get(skill, 0) + 1

        # Sort skills by frequency
        skill_labels = sorted(all_skills.keys(), key=lambda s: all_skills[s], reverse=True)
        skill_counts = [all_skills[s] for s in skill_labels]

        context = {
            "candidates": candidates,
            "total_candidates": total,
            "completed_count": len(completed),
            "error_count": len(errors),
            "avg_score": avg_score,
            "top_score": top_score,
            "skill_labels": skill_labels,
            "skill_counts": skill_counts,
            # Data for Chart.js (JSON-safe lists)
            "chart_names": [c["candidate_name"] for c in completed],
            "chart_scores": [c["score"] for c in completed],
        }

        return render(request, "dashboard/results.html", context)

    except Exception as e:
        logger.exception("Error loading dashboard results: %s", str(e))
        return render(request, "dashboard/results.html", {
            "candidates": [],
            "total_candidates": 0,
            "completed_count": 0,
            "error_count": 0,
            "avg_score": 0,
            "top_score": 0,
            "skill_labels": [],
            "skill_counts": [],
            "chart_names": [],
            "chart_scores": [],
            "error_message": "Failed to load dashboard data. Please try again.",
        })


def candidate_detail(request, candidate_id):
    """
    Display detailed gap analysis for a single candidate.

    GET /dashboard/candidate/<id>/
    """
    try:
        if USE_MOCK:
            detail = get_mock_candidate_detail(candidate_id)
        else:
            # TODO: Replace with real DB read + fastapi_client.get_gap_analysis()
            detail = get_mock_candidate_detail(candidate_id)

        if detail is None:
            raise Http404(f"Candidate {candidate_id} not found")

        # Separate skills by proficiency level for the radar chart
        proficiency_map = {"expert": 5, "advanced": 4, "intermediate": 3, "beginner": 2}
        skill_names = [s["skill"] for s in detail.get("matched_skills", [])]
        skill_levels = [
            proficiency_map.get(s.get("proficiency", "intermediate"), 3)
            for s in detail.get("matched_skills", [])
        ]

        # Gap importance for chart
        gap_names = [g["skill"] for g in detail.get("gaps", [])]
        importance_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        gap_importances = [
            importance_map.get(g.get("importance", "medium"), 2)
            for g in detail.get("gaps", [])
        ]

        context = {
            "candidate": detail,
            "skill_names": skill_names,
            "skill_levels": skill_levels,
            "gap_names": gap_names,
            "gap_importances": gap_importances,
        }

        return render(request, "dashboard/candidate_detail.html", context)

    except Http404:
        raise
    except Exception as e:
        logger.exception(
            "Error loading candidate %d detail: %s", candidate_id, str(e)
        )
        return render(request, "dashboard/candidate_detail.html", {
            "candidate": None,
            "error_message": "Failed to load candidate details. Please try again.",
        })


# ---------------------------------------------------------------------------
# Feedback Loop endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def submit_feedback(request):
    """
    Accept recruiter feedback on a candidate match.

    POST /dashboard/feedback/
    Body (JSON): {match_id, recruiter_id, feedback, skill_snapshot}
    """
    try:
        data = json.loads(request.body)
        match_id = data.get("match_id")
        recruiter_id = int(data.get("recruiter_id", 0))
        feedback = data.get("feedback")
        skill_snapshot = data.get("skill_snapshot", [])

        if not match_id or feedback not in ("good_fit", "not_a_fit"):
            return JsonResponse(
                {"status": "error", "message": "match_id and valid feedback required"},
                status=400,
            )

        record_feedback(match_id, recruiter_id, feedback, skill_snapshot)
        return JsonResponse({"status": "ok"})

    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400,
        )
    except Exception as e:
        logger.exception("Error processing feedback: %s", str(e))
        return JsonResponse(
            {"status": "error", "message": "Internal server error"},
            status=500,
        )
