"""
Data layer — loads real results from results.json (with fallback to mock data).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("dashboard")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MOCK_CANDIDATES = [
    {
        "resume_id": "res_001",
        "candidate_name": "Rahul Sharma",
        "email": "rahul.sharma@gmail.com",
        "resume_filename": "rahul_sharma.pdf",
        "job_description_id": "jd_203",
        "job_title": "Backend Engineer",
        "status": "scored",
        "overall_match_percentage": 82.47,
        "vector_similarity_score": 0.874,
        "analysis": {
            "matched_skills": ["python", "sql", "fastapi", "docker"],
            "partial_skills": [],
            "missing_skills": ["aws"],
            "strengths": ["python", "sql", "fastapi", "docker"],
            "gaps": ["aws"],
            "ai_rationale": "Candidate matches 4 of 5 required skills. Hybrid match score is 82.47%.",
            "hiring_recommendation": "Shortlist"
        },
        "processed_at": "2026-08-12T05:25:31.482913+00:00",
        "rank": 1
    }
]

def load_results_json() -> list[dict] | None:
    """Find and load results.json file from output, data, or root directory."""
    possible_files = [
        BASE_DIR / "results.json",
        BASE_DIR / "output" / "results.json",
        BASE_DIR / "data" / "results.json",
        Path.cwd() / "results.json",
        Path.cwd() / "output" / "results.json"
    ]
    for filepath in possible_files:
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception as e:
                logger.error("Error reading %s: %s", filepath, e)
    return None

def _map_candidate_schema(c: dict) -> dict:
    """Maps API/results.json schema to what dashboard templates expect."""
    analysis = c.get("analysis") or {}
    matched = analysis.get("matched_skills") or []
    missing = analysis.get("missing_skills") or analysis.get("gaps") or []
    rationale = analysis.get("ai_rationale") or f"Match score: {c.get('overall_match_percentage', 0)}%"

    return {
        "candidate_id": str(c.get("resume_id", "")),
        "candidate_name": c.get("candidate_name") or "Candidate",
        "email": c.get("email") or "",
        "resume_id": str(c.get("resume_id", "")),
        "score": int(c.get("overall_match_percentage", 0)),
        "matched_skills": matched,
        "gaps": missing,
        "insight_text": rationale,
        "status": "completed" if c.get("status") == "scored" else c.get("status", "completed"),
    }

def get_candidates():
    """Return all candidates from results.json (or mock if results.json not present)."""
    raw_results = load_results_json()
    if not raw_results:
        raw_results = MOCK_CANDIDATES

    mapped = [_map_candidate_schema(c) for c in raw_results]
    return sorted(mapped, key=lambda c: c["score"], reverse=True)

def get_candidate_detail(candidate_id: str):
    """Return detailed gap analysis for a single candidate from results.json."""
    raw_results = load_results_json()
    if not raw_results:
        raw_results = MOCK_CANDIDATES

    for c in raw_results:
        if str(c.get("resume_id")) == str(candidate_id):
            detail = _map_candidate_schema(c)
            analysis = c.get("analysis") or {}

            matched_skills_list = analysis.get("matched_skills") or []
            detail["matched_skills"] = [
                {"skill": str(s), "proficiency": "expert", "evidence": "Matched by AI"}
                for s in matched_skills_list
            ]

            for ps in analysis.get("partial_skills", []):
                if isinstance(ps, dict):
                    detail["matched_skills"].append({
                        "skill": ps.get("required_skill", "Skill"),
                        "proficiency": "intermediate",
                        "evidence": f"Has {ps.get('resume_skill', '')} ({int(ps.get('similarity', 0)*100)}% match)"
                    })
                elif isinstance(ps, str):
                    detail["matched_skills"].append({
                        "skill": ps,
                        "proficiency": "intermediate",
                        "evidence": "Partial match"
                    })

            gaps_list = analysis.get("missing_skills") or analysis.get("gaps") or []
            detail["gaps"] = [
                {"skill": str(s), "importance": "high", "recommendation": "Skill missing from resume"}
                for s in gaps_list
            ]

            detail["experience_years"] = 0
            detail["education"] = "Not specified"
            return detail

    return None

# Backward compatibility aliases
get_mock_candidates = get_candidates
get_mock_candidate_detail = get_candidate_detail
