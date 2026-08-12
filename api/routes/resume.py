"""
Resume endpoints — parse-resume.

POST /parse-resume    → Return structured resume data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.data.store import get_result_by_id

router = APIRouter(tags=["Resume"])


class ParseRequest(BaseModel):
    resume_id: str


@router.post("/parse-resume")
async def parse_resume(request: ParseRequest):
    """Return structured resume data for a given resume_id."""
    result = get_result_by_id(request.resume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Resume {request.resume_id} not found")

    # Return the subset of fields relevant to resume parsing
    return {
        "resume_id": result["resume_id"],
        "candidate_name": result["candidate_name"],
        "email": result["email"],
        "resume_filename": result["resume_filename"],
        "skills": result["analysis"]["matched_skills"],
    }
