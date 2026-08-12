"""
Resume endpoints.

POST /parse-resume
    Upload one PDF and return structured resume data.

POST /parse-resumes
    Upload multiple PDFs and return structured resume data
    for each resume.
"""

import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from resume_processing.pdf_parser import extract_resume
from resume_processing.groq_extractor import GroqResumeExtractor


router = APIRouter(tags=["Resume"])


# ============================================================
# GROQ INITIALIZATION
# ============================================================

try:
    groq_extractor = GroqResumeExtractor()

except Exception as exc:
    groq_extractor = None
    GROQ_INIT_ERROR = str(exc)


# ============================================================
# POST /parse-resume
# Process ONE resume
# ============================================================

@router.post("/parse-resume")
async def parse_resume(
    file: UploadFile = File(...)
):
    """
    Upload one PDF resume, extract its text using PyMuPDF,
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

        # Preserve original filename
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


# ============================================================
# POST /parse-resumes
# Process MULTIPLE resumes
# ============================================================

@router.post("/parse-resumes")
async def parse_resumes(
    files: list[UploadFile] = File(...)
):
    """
    Upload multiple PDF resumes and return structured
    resume information for each file.
    """

    # -----------------------------------------
    # 1. Validate uploaded files
    # -----------------------------------------

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No resume files were uploaded."
        )

    if groq_extractor is None:
        raise HTTPException(
            status_code=500,
            detail=f"Groq initialization failed: {GROQ_INIT_ERROR}"
        )

    results = []

    # -----------------------------------------
    # 2. Process each resume
    # -----------------------------------------

    for file in files:

        temp_path = None

        try:

            # -----------------------------------------
            # Validate filename
            # -----------------------------------------

            if not file.filename:

                results.append({
                    "filename": None,
                    "status": "failed",
                    "error": "No filename provided."
                })

                continue

            # -----------------------------------------
            # Validate PDF
            # -----------------------------------------

            if not file.filename.lower().endswith(".pdf"):

                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": "Only PDF files are supported."
                })

                continue

            # -----------------------------------------
            # Save PDF temporarily
            # -----------------------------------------

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                temp_path = temp_file.name

                content = await file.read()

                if not content:

                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": "Uploaded PDF is empty."
                    })

                    continue

                temp_file.write(content)

            # -----------------------------------------
            # Extract PDF using PyMuPDF
            # -----------------------------------------

            extracted_data = extract_resume(
                temp_path
            )

            if extracted_data["document"]["status"] != "success":

                results.append({
                    "resume_id": extracted_data.get(
                        "resume_id"
                    ),
                    "filename": file.filename,
                    "status": "failed",
                    "error": extracted_data.get(
                        "error",
                        "Could not extract text from PDF."
                    )
                })

                continue

            # Preserve original filename
            extracted_data["file"]["filename"] = (
                file.filename
            )

            # -----------------------------------------
            # Structure resume using Groq
            # -----------------------------------------

            structured_data = groq_extractor.extract(
                extracted_data
            )

            # -----------------------------------------
            # Preserve metadata
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

            # Add successful result
            results.append(
                structured_data
            )

        except Exception as exc:

            # -----------------------------------------
            # Don't stop the whole batch if one
            # resume fails
            # -----------------------------------------

            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(exc)
            })

        finally:

            # -----------------------------------------
            # Remove temporary PDF
            # -----------------------------------------

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    # -----------------------------------------
    # 3. Calculate statistics
    # -----------------------------------------

    successful = sum(
        1
        for result in results
        if result.get("status") == "success"
    )

    failed = sum(
        1
        for result in results
        if result.get("status") == "failed"
    )

    # -----------------------------------------
    # 4. Return batch response
    # -----------------------------------------

    return {
        "total_resumes": len(results),
        "successful": successful,
        "failed": failed,
        "resumes": results
    }