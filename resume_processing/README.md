# Resume Processing Module

## Overview

This module is responsible for extracting and structuring information
from candidate resumes for the AI Resume Screening Assistant.

The module processes PDF resumes, extracts their content, and uses an
LLM to convert the extracted resume information into structured JSON.

## Processing Pipeline

PDF Resume
    ↓
PyMuPDF (fitz)
    ↓
Text Extraction
    ↓
Raw Resume JSON
    ↓
Groq / Llama LLM
    ↓
Structured Resume JSON

## Responsibilities

This module handles:

- PDF resume processing
- Multi-page PDF text extraction
- Resume metadata extraction
- Candidate name extraction
- Candidate email extraction
- Resume section identification
- Skill extraction
- Structured resume information extraction
- Batch processing of multiple resumes
- JSON output generation

## Technologies Used

### Python

Main programming language used for the resume processing pipeline.

### PyMuPDF (fitz)

Used to:

- Open PDF files
- Process multiple pages
- Extract text from each page
- Preserve page-wise text
- Obtain the total number of pages

### Groq / Llama

Used for semantic structuring of extracted resume information.

The LLM converts raw resume text into structured fields such as:

- Candidate information
- Skills
- Work experience
- Education
- Projects
- Certifications
- Achievements
- Publications
- Languages
- Coursework
- Professional links

### JSON

Used as the interface format between the resume processing stages
and other components of the application.

## Input

The module currently accepts PDF resumes placed inside:

    test_resumes/

Example:

    test_resumes/
    ├── resume1.pdf
    ├── resume2.pdf
    └── resume3.pdf

## Output

### Raw Extraction

The first stage produces:

    output/extracted_resumes.json

This contains:

- Resume ID
- Filename
- File hash
- Page count
- Candidate information
- Page-wise extracted text
- Complete extracted text
- Detected resume sections
- Processing status

### Structured Extraction

The Groq processing stage produces:

    output/structured_resumes.json

Example structure:

```json
{
    "resume_id": "a81f42c9d31e72ab",
    "filename": "candidate.pdf",
    "page_count": 2,

    "candidate": {
        "name": "John Doe",
        "email": "john@example.com"
    },

    "summary": "Backend developer with experience in Python.",

    "skills": [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "AWS"
    ],

    "experience": [
        {
            "company": "ABC Technologies",
            "role": "Software Engineer",
            "location": null,
            "start_date": "2025",
            "end_date": "2026",
            "duration": null,
            "responsibilities": [
                "Developed REST APIs"
            ],
            "technologies_used": [
                "Python",
                "FastAPI"
            ]
        }
    ],

    "education": [],
    "projects": [],
    "certifications": [],
    "achievements": [],
    "publications": [],
    "languages": [],
    "coursework": [],

    "links": {
        "linkedin": null,
        "github": null,
        "portfolio": null,
        "other": []
    },

    "status": "success"
}