from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.data.store import get_all_results, get_result_by_id

router = APIRouter(tags=["Matching"])

class MatchRequest(BaseModel):
    resume_id: Optional[str] = None
    jd_id: Optional[str] = None
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None

@router.post("/match-score")
async def match_score(request: MatchRequest):
    """Return the scoring result for a resume/JD pair or candidate ID."""
    if request.resume_id:
        result = get_result_by_id(request.resume_id)
        if result:
            return result
    
    results = get_all_results()
    if results:
        return results[0]
        
    raise HTTPException(status_code=404, detail="No candidate results found")

@router.post("/gap-analysis")
async def gap_analysis(request: MatchRequest):
    """Return gap analysis for a resume/JD pair or candidate ID."""
    if request.resume_id:
        result = get_result_by_id(request.resume_id)
        if result:
            return result
            
    results = get_all_results()
    if results:
        return results[0]
        
    raise HTTPException(status_code=404, detail="No candidate results found")
