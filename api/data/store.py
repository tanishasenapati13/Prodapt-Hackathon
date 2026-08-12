"""
In-memory data store — pre-loaded with the scored candidate results.

The dashboard calls these endpoints to fetch data. No scoring logic here;
Person 2's backend handles the actual matching. This just serves results.
"""

from datetime import datetime, timezone

# ── Pre-loaded scored results (exact shape from Person 2's backend) ──

SCORED_RESULTS = [
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
    },
    {
        "resume_id": "res_002",
        "candidate_name": "Priya Menon",
        "email": "priya.menon@gmail.com",
        "resume_filename": "priya_menon.pdf",
        "job_description_id": "jd_203",
        "job_title": "Backend Engineer",
        "status": "scored",
        "overall_match_percentage": 74.31,
        "vector_similarity_score": 0.808,
        "analysis": {
            "matched_skills": ["python", "sql", "docker"],
            "partial_skills": [
                {
                    "required_skill": "fastapi",
                    "resume_skill": "flask",
                    "similarity": 0.734
                }
            ],
            "missing_skills": ["aws"],
            "strengths": ["python", "sql", "docker"],
            "gaps": ["aws"],
            "ai_rationale": "Candidate matches 3 of 5 required skills. Hybrid match score is 74.31%.",
            "hiring_recommendation": "Consider"
        },
        "processed_at": "2026-08-12T05:25:32.129482+00:00",
        "rank": 2
    },
    {
        "resume_id": "res_003",
        "candidate_name": "Arjun Kapoor",
        "email": "arjun.kapoor@gmail.com",
        "resume_filename": "arjun_kapoor.pdf",
        "job_description_id": "jd_203",
        "job_title": "Backend Engineer",
        "status": "scored",
        "overall_match_percentage": 58.62,
        "vector_similarity_score": 0.692,
        "analysis": {
            "matched_skills": ["python", "sql"],
            "partial_skills": [
                {
                    "required_skill": "fastapi",
                    "resume_skill": "flask",
                    "similarity": 0.721
                }
            ],
            "missing_skills": ["docker", "aws"],
            "strengths": ["python", "sql"],
            "gaps": ["docker", "aws"],
            "ai_rationale": "Candidate matches 2 of 5 required skills. Hybrid match score is 58.62%.",
            "hiring_recommendation": "Reject"
        },
        "processed_at": "2026-08-12T05:25:33.742891+00:00",
        "rank": 3
    }
]

# Index by resume_id for O(1) lookup
_results_by_id = {r["resume_id"]: r for r in SCORED_RESULTS}


def get_all_results() -> list[dict]:
    """Return all scored results, sorted by rank."""
    return sorted(SCORED_RESULTS, key=lambda r: r["rank"])


def get_result_by_id(resume_id: str) -> dict | None:
    """Return a single scored result by resume_id."""
    return _results_by_id.get(resume_id)
