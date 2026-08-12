import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# DEFAULT_MOCK_RESULTS = [
#     {
#         "resume_id": "res_001",
#         "candidate_name": "Rahul Sharma",
#         "email": "rahul.sharma@gmail.com",
#         "resume_filename": "rahul_sharma.pdf",
#         "job_description_id": "jd_203",
#         "job_title": "Backend Engineer",
#         "status": "scored",
#         "overall_match_percentage": 82.47,
#         "vector_similarity_score": 0.874,
#         "analysis": {
#             "matched_skills": ["python", "sql", "fastapi", "docker"],
#             "partial_skills": [],
#             "missing_skills": ["aws"],
#             "strengths": ["python", "sql", "fastapi", "docker"],
#             "gaps": ["aws"],
#             "ai_rationale": "Candidate matches 4 of 5 required skills. Hybrid match score is 82.47%.",
#             "hiring_recommendation": "Shortlist"
#         },
#         "processed_at": "2026-08-12T05:25:31.482913+00:00",
#         "rank": 1
#     }
# ]

def load_scored_results() -> list[dict]:
    with open("results.json", "r", encoding="utf-8") as f:
        results = json.load(f)
    print(f"Loaded {len(results)} scored results from results.json")
    return results

# Dynamic SCORED_RESULTS property fallback
SCORED_RESULTS = load_scored_results()

def get_all_results() -> list[dict]:
    return load_scored_results()

def get_result_by_id(resume_id: str) -> dict | None:
    results = load_scored_results()
    for r in results:
        if str(r.get("resume_id")) == str(resume_id):
            return r
    return None
