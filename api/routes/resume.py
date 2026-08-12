"""
Resume endpoints.

POST /parse-resume -> Upload one PDF and return structured resume data
"""

import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from resume_processing.pdf_parser import extract_resume
from resume_processing.groq_extractor import GroqResumeExtractor


router = APIRouter(tags=["Resume"])


# Initialize Groq once when the API starts.
try:
    groq_extractor = GroqResumeExtractor()
except Exception as exc:
    groq_extractor = None
    GROQ_INIT_ERROR = str(exc)


@router.post("/parse-resume")
async def parse_resume(
    file: UploadFile = File(...)
):
    """
    Upload a PDF resume, extract its text using PyMuPDF,
    structure the information using Groq, and return JSON.
    """

    # -----------------------------------------
    # 1. Validate uploaded file
    # -----------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    if groq_extractor is None:
        raise HTTPException(
            status_code=500,
            detail=f"Groq initialization failed: {GROQ_INIT_ERROR}"
        )

    temp_path = None

    try:

        # -----------------------------------------
        # 2. Save uploaded PDF temporarily
        # -----------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:

            temp_path = temp_file.name

            content = await file.read()

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF is empty."
                )

            temp_file.write(content)

        # -----------------------------------------
        # 3. Extract resume using PyMuPDF
        # -----------------------------------------

        extracted_data = extract_resume(
            temp_path
        )

        if extracted_data["document"]["status"] != "success":

            raise HTTPException(
                status_code=422,
                detail=extracted_data.get(
                    "error",
                    "Could not extract text from PDF."
                )
            )

        # Preserve original filename.
        extracted_data["file"]["filename"] = (
            file.filename
        )

        # -----------------------------------------
        # 4. Structure resume using Groq
        # -----------------------------------------

        structured_data = groq_extractor.extract(
            extracted_data
        )

        # -----------------------------------------
        # 5. Preserve metadata
        # -----------------------------------------

        structured_data["resume_id"] = (
            extracted_data["resume_id"]
        )

        structured_data["filename"] = (
            file.filename
        )

        structured_data["page_count"] = (
            extracted_data["document"]["page_count"]
        )

        structured_data["status"] = "success"

        # -----------------------------------------
        # 6. Return structured JSON
        # -----------------------------------------

        return structured_data

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(exc)}"
        )

    finally:

        # -----------------------------------------
        # 7. Remove temporary PDF
        # -----------------------------------------

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)