"""
Mock data layer — returns fake results shaped exactly like Person 2's
FastAPI responses and Person 3's DB rows.

Usage:
    from dashboard.services.mock_data import get_mock_candidates, get_mock_candidate_detail

Swap to real data by changing imports in views.py — zero template changes needed.
"""

MOCK_CANDIDATES = [
    {
        "candidate_id": 1,
        "candidate_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "resume_id": 101,
        "score": 92,
        "matched_skills": ["Python", "Django", "REST APIs", "PostgreSQL", "Docker"],
        "gaps": ["Kubernetes", "GraphQL"],
        "insight_text": (
            "Exceptional backend fit with strong Python/Django experience. "
            "Production-ready REST API skills. Would benefit from container "
            "orchestration and GraphQL exposure for senior-level readiness."
        ),
        "status": "completed",
    },
    {
        "candidate_id": 2,
        "candidate_name": "Alex Rivera",
        "email": "alex.rivera@example.com",
        "resume_id": 102,
        "score": 78,
        "matched_skills": ["Python", "FastAPI", "SQL", "Git"],
        "gaps": ["Django", "Docker", "CI/CD"],
        "insight_text": (
            "Strong Python fundamentals with FastAPI experience. "
            "Lacks Django-specific knowledge but transferable skills are solid. "
            "Needs containerization and deployment pipeline exposure."
        ),
        "status": "completed",
    },
    {
        "candidate_id": 3,
        "candidate_name": "Morgan Chen",
        "email": "morgan.chen@example.com",
        "resume_id": 103,
        "score": 85,
        "matched_skills": ["Python", "Django", "React", "PostgreSQL", "AWS"],
        "gaps": ["GraphQL"],
        "insight_text": (
            "Full-stack profile with strong backend and frontend skills. "
            "Cloud experience with AWS is a significant plus. "
            "Minor gap in GraphQL, easily addressable."
        ),
        "status": "completed",
    },
    {
        "candidate_id": 4,
        "candidate_name": "Sam Patel",
        "email": "sam.patel@example.com",
        "resume_id": 104,
        "score": 65,
        "matched_skills": ["JavaScript", "Node.js", "MongoDB"],
        "gaps": ["Python", "Django", "PostgreSQL", "REST APIs"],
        "insight_text": (
            "Primarily a JavaScript/Node.js developer. "
            "Significant gaps in the Python ecosystem required for this role. "
            "Would need substantial ramp-up time."
        ),
        "status": "completed",
    },
    {
        "candidate_id": 5,
        "candidate_name": "Taylor Kim",
        "email": "taylor.kim@example.com",
        "resume_id": 105,
        "score": 88,
        "matched_skills": ["Python", "Django", "Docker", "Kubernetes", "CI/CD", "PostgreSQL"],
        "gaps": ["GraphQL"],
        "insight_text": (
            "Strong DevOps-oriented backend developer. Excellent infrastructure "
            "skills combined with solid Django experience. Near-perfect match "
            "for the role requirements."
        ),
        "status": "completed",
    },
    {
        "candidate_id": 6,
        "candidate_name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "resume_id": 106,
        "score": 0,
        "matched_skills": [],
        "gaps": [],
        "insight_text": "Resume could not be parsed — file appears to be corrupted or empty.",
        "status": "error",
        "error": "parsing_failed",
    },
]

# Detailed gap analysis for candidate detail view
MOCK_GAP_ANALYSES = {
    1: {
        "candidate_id": 1,
        "candidate_name": "Jane Doe",
        "score": 92,
        "matched_skills": [
            {"skill": "Python", "proficiency": "expert", "evidence": "5+ years, multiple production projects"},
            {"skill": "Django", "proficiency": "advanced", "evidence": "Built 3 production Django apps"},
            {"skill": "REST APIs", "proficiency": "advanced", "evidence": "Designed RESTful services at scale"},
            {"skill": "PostgreSQL", "proficiency": "intermediate", "evidence": "Query optimization, schema design"},
            {"skill": "Docker", "proficiency": "intermediate", "evidence": "Dockerized applications for deployment"},
        ],
        "gaps": [
            {"skill": "Kubernetes", "importance": "medium", "recommendation": "Consider CKA certification or hands-on project"},
            {"skill": "GraphQL", "importance": "low", "recommendation": "Supplementary skill — online course sufficient"},
        ],
        "insight_text": (
            "Exceptional backend fit with strong Python/Django experience. "
            "Production-ready REST API skills. Would benefit from container "
            "orchestration and GraphQL exposure for senior-level readiness."
        ),
        "experience_years": 6,
        "education": "M.S. Computer Science, Stanford University",
    },
    2: {
        "candidate_id": 2,
        "candidate_name": "Alex Rivera",
        "score": 78,
        "matched_skills": [
            {"skill": "Python", "proficiency": "advanced", "evidence": "4 years professional experience"},
            {"skill": "FastAPI", "proficiency": "advanced", "evidence": "Primary framework in current role"},
            {"skill": "SQL", "proficiency": "intermediate", "evidence": "Complex query writing, joins, indexing"},
            {"skill": "Git", "proficiency": "advanced", "evidence": "Daily workflow with branching strategies"},
        ],
        "gaps": [
            {"skill": "Django", "importance": "high", "recommendation": "Core framework for this role — structured learning recommended"},
            {"skill": "Docker", "importance": "medium", "recommendation": "Containerization fundamentals needed"},
            {"skill": "CI/CD", "importance": "medium", "recommendation": "Set up a pipeline for a personal project"},
        ],
        "insight_text": (
            "Strong Python fundamentals with FastAPI experience. "
            "Lacks Django-specific knowledge but transferable skills are solid. "
            "Needs containerization and deployment pipeline exposure."
        ),
        "experience_years": 4,
        "education": "B.S. Software Engineering, UC Berkeley",
    },
    3: {
        "candidate_id": 3,
        "candidate_name": "Morgan Chen",
        "score": 85,
        "matched_skills": [
            {"skill": "Python", "proficiency": "advanced", "evidence": "3+ years in data-heavy applications"},
            {"skill": "Django", "proficiency": "intermediate", "evidence": "2 production Django projects"},
            {"skill": "React", "proficiency": "advanced", "evidence": "Primary frontend framework"},
            {"skill": "PostgreSQL", "proficiency": "advanced", "evidence": "Database administration experience"},
            {"skill": "AWS", "proficiency": "intermediate", "evidence": "EC2, S3, RDS deployments"},
        ],
        "gaps": [
            {"skill": "GraphQL", "importance": "low", "recommendation": "Nice to have — Apollo/Graphene intro course"},
        ],
        "insight_text": (
            "Full-stack profile with strong backend and frontend skills. "
            "Cloud experience with AWS is a significant plus. "
            "Minor gap in GraphQL, easily addressable."
        ),
        "experience_years": 5,
        "education": "B.S. Computer Science, MIT",
    },
    4: {
        "candidate_id": 4,
        "candidate_name": "Sam Patel",
        "score": 65,
        "matched_skills": [
            {"skill": "JavaScript", "proficiency": "expert", "evidence": "6 years full-stack JS development"},
            {"skill": "Node.js", "proficiency": "advanced", "evidence": "Built microservices architecture"},
            {"skill": "MongoDB", "proficiency": "advanced", "evidence": "NoSQL schema design and optimization"},
        ],
        "gaps": [
            {"skill": "Python", "importance": "critical", "recommendation": "Must-have for this role — structured learning path required"},
            {"skill": "Django", "importance": "critical", "recommendation": "Primary framework — Django tutorial + project"},
            {"skill": "PostgreSQL", "importance": "high", "recommendation": "SQL fundamentals needed, transition from NoSQL"},
            {"skill": "REST APIs", "importance": "medium", "recommendation": "Has Express.js REST experience — transferable with guidance"},
        ],
        "insight_text": (
            "Primarily a JavaScript/Node.js developer. "
            "Significant gaps in the Python ecosystem required for this role. "
            "Would need substantial ramp-up time."
        ),
        "experience_years": 6,
        "education": "B.Tech Information Technology, IIT Delhi",
    },
    5: {
        "candidate_id": 5,
        "candidate_name": "Taylor Kim",
        "score": 88,
        "matched_skills": [
            {"skill": "Python", "proficiency": "advanced", "evidence": "4+ years automation and backend"},
            {"skill": "Django", "proficiency": "advanced", "evidence": "Lead developer on Django monolith"},
            {"skill": "Docker", "proficiency": "expert", "evidence": "Production container orchestration"},
            {"skill": "Kubernetes", "proficiency": "advanced", "evidence": "Managed K8s clusters in production"},
            {"skill": "CI/CD", "proficiency": "expert", "evidence": "Built CI/CD pipelines with GitHub Actions"},
            {"skill": "PostgreSQL", "proficiency": "intermediate", "evidence": "Standard CRUD + migrations"},
        ],
        "gaps": [
            {"skill": "GraphQL", "importance": "low", "recommendation": "Optional nice-to-have — quick ramp-up possible"},
        ],
        "insight_text": (
            "Strong DevOps-oriented backend developer. Excellent infrastructure "
            "skills combined with solid Django experience. Near-perfect match "
            "for the role requirements."
        ),
        "experience_years": 5,
        "education": "M.S. Computer Engineering, Georgia Tech",
    },
}


def get_mock_candidates():
    """Return all mock candidates, sorted by score descending."""
    return sorted(MOCK_CANDIDATES, key=lambda c: c["score"], reverse=True)


def get_mock_candidate_detail(candidate_id: int):
    """Return detailed gap analysis for a single candidate."""
    return MOCK_GAP_ANALYSES.get(candidate_id)


def get_mock_match_result(resume_id: int, jd_id: int):
    """
    Simulate a /match-score API response.
    Shaped exactly like Person 2's FastAPI contract.
    """
    # Return a result based on resume_id for deterministic testing
    for candidate in MOCK_CANDIDATES:
        if candidate["resume_id"] == resume_id:
            return {
                "resume_id": resume_id,
                "jd_id": jd_id,
                "candidate_name": candidate["candidate_name"],
                "score": candidate["score"],
                "matched_skills": candidate["matched_skills"],
                "gaps": candidate["gaps"],
                "insight_text": candidate["insight_text"],
            }
    # Fallback for unknown resume_id
    return {
        "resume_id": resume_id,
        "jd_id": jd_id,
        "candidate_name": "Unknown Candidate",
        "score": 50,
        "matched_skills": ["Python"],
        "gaps": ["Django", "Docker"],
        "insight_text": "Limited data available for scoring.",
    }


def get_mock_gap_analysis(resume_id: int, jd_id: int):
    """
    Simulate a /gap-analysis API response.
    """
    for cid, detail in MOCK_GAP_ANALYSES.items():
        candidates = [c for c in MOCK_CANDIDATES if c["candidate_id"] == cid]
        if candidates and candidates[0]["resume_id"] == resume_id:
            return detail
    return None
