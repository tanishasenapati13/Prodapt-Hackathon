"""
Mock data layer — returns fake results shaped exactly like Person 2's
FastAPI responses and Person 3's DB rows.

Usage:
    from dashboard.services.mock_data import get_mock_candidates, get_mock_candidate_detail

Swap to real data by changing imports in views.py — zero template changes needed.
"""

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


def _map_candidate_schema(c):
    """Maps the new API JSON schema to what the dashboard templates expect."""
    return {
        "candidate_id": c["resume_id"],  # String IDs now
        "candidate_name": c["candidate_name"],
        "email": c["email"],
        "resume_id": c["resume_id"],
        "score": int(c["overall_match_percentage"]),
        "matched_skills": c["analysis"]["matched_skills"],
        "gaps": c["analysis"].get("missing_skills", []) or c["analysis"].get("gaps", []),
        "insight_text": c["analysis"]["ai_rationale"],
        "status": c["status"] if c["status"] != "scored" else "completed",
    }


def get_mock_candidates():
    """Return all mock candidates, mapped to the template schema."""
    mapped = [_map_candidate_schema(c) for c in MOCK_CANDIDATES]
    return sorted(mapped, key=lambda c: c["score"], reverse=True)


def get_mock_candidate_detail(candidate_id: str):
    """Return detailed gap analysis for a single candidate."""
    for c in MOCK_CANDIDATES:
        if c["resume_id"] == candidate_id:
            detail = _map_candidate_schema(c)
            # Add detailed proficiency maps for the charts
            detail["matched_skills"] = [
                {"skill": s, "proficiency": "expert", "evidence": "Matched by AI"} 
                for s in c["analysis"]["matched_skills"]
            ]
            
            # Incorporate partial skills as intermediate
            for ps in c["analysis"].get("partial_skills", []):
                detail["matched_skills"].append({
                    "skill": ps["required_skill"],
                    "proficiency": "intermediate", 
                    "evidence": f"Has {ps['resume_skill']} ({int(ps['similarity']*100)}% match)"
                })

            detail["gaps"] = [
                {"skill": s, "importance": "high", "recommendation": "Skill missing from resume"} 
                for s in (c["analysis"].get("missing_skills", []) or c["analysis"].get("gaps", []))
            ]
            
            detail["experience_years"] = 0 # Not provided in new schema
            detail["education"] = "Not specified" 
            return detail
            
    return None
