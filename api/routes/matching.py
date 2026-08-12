"""
Matching endpoints — serve match-score and gap-analysis results.

POST /match-score     → Score result for a resume/JD pair
POST /gap-analysis    → Gap analysis for a resume/JD pair (same data)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.data.store import get_result_by_id

router = APIRouter(tags=["Matching"])


class MatchRequest(BaseModel):
    resume_id: str
    jd_id: str


@router.post("/match-score")
async def match_score(request: MatchRequest):
    """Return the scoring result for a resume/JD pair."""
    result = get_result_by_id(request.resume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Resume {request.resume_id} not found")
    return result


@router.post("/gap-analysis")
async def gap_analysis(request: MatchRequest):
    """Return gap analysis for a resume/JD pair (same data as match-score)."""
    result = get_result_by_id(request.resume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Resume {request.resume_id} not found")
    return result
