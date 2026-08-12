from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.data.store import get_all_results, get_result_by_id

router = APIRouter(tags=["Resume"])

class ParseRequest(BaseModel):
    resume_id: Optional[str] = None
    resume_text: Optional[str] = None

@router.post("/parse-resume")
async def parse_resume(request: ParseRequest):
    """Return structured resume data for a given resume_id or default top candidate."""
    result = None
    if request.resume_id:
        result = get_result_by_id(request.resume_id)
        
    if not result:
        results = get_all_results()
        if results:
            result = results[0]

    if not result:
        raise HTTPException(status_code=404, detail="No resume data found")

    analysis = result.get("analysis", {})
    return {
        "resume_id": result.get("resume_id"),
        "candidate_name": result.get("candidate_name"),
        "email": result.get("email"),
        "resume_filename": result.get("resume_filename"),
        "skills": analysis.get("matched_skills", []),
        "strengths": analysis.get("strengths", []),
        "gaps": analysis.get("gaps", []),
        "overall_match_percentage": result.get("overall_match_percentage")
    }
