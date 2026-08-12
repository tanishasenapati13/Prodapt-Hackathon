"""
Candidate endpoints — serve scored results to the dashboard.

GET  /candidates          → Ranked list of all scored candidates
GET  /candidates/{id}     → Single candidate result
"""

from fastapi import APIRouter, HTTPException
from api.data.store import get_all_results, get_result_by_id

router = APIRouter(tags=["Candidates"])


@router.get("/candidates")
async def list_candidates():
    """Return all scored candidates, ranked by match percentage."""
    return get_all_results()


@router.get("/candidates/{resume_id}")
async def get_candidate(resume_id: str):
    """Return a single candidate's scoring result."""
    result = get_result_by_id(resume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Candidate {resume_id} not found")
    return result
