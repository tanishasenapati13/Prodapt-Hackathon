from pathlib import Path
import hashlib
import re
import fitz


def calculate_file_hash(file_path: str) -> str:
    """Generate SHA-256 hash for the PDF."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def extract_email(text: str):
    """Extract email addresses."""

    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return list(dict.fromkeys(emails))


def extract_name(text: str):
    """
    Basic name extraction.

    Assumes the candidate name is usually near
    the beginning of the resume.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    for line in lines[:10]:

        if "@" in line:
            continue

        if any(char.isdigit() for char in line):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:

            if all(
                word.replace("-", "").isalpha()
                for word in words
            ):
                return line

    return None


def extract_sections(text: str):
    """
    Identify common resume sections and preserve
    their extracted text.
    """

    section_patterns = {
        "summary": [
            "summary",
            "professional summary",
            "profile",
            "objective"
        ],

        "skills": [
            "skills",
            "technical skills",
            "core skills",
            "technical expertise"
        ],

        "experience": [
            "experience",
            "work experience",
            "professional experience",
            "employment history"
        ],

        "education": [
            "education",
            "academic background",
            "educational qualifications"
        ],

        "projects": [
            "projects",
            "academic projects",
            "personal projects"
        ],

        "certifications": [
            "certifications",
            "certificates"
        ],

        "achievements": [
            "achievements",
            "awards",
            "honors"
        ],

        "languages": [
            "languages",
            "language proficiency"
        ]
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    sections = {}

    current_section = "other"
    sections[current_section] = []

    for line in lines:

        normalized = line.lower().strip()
        normalized = normalized.rstrip(":").strip()

        detected_section = None

        for section_name, headings in section_patterns.items():

            if normalized in headings:
                detected_section = section_name
                break

        if detected_section:

            current_section = detected_section

            if current_section not in sections:
                sections[current_section] = []

        else:

            sections.setdefault(
                current_section,
                []
            ).append(line)

    for key in sections:

        sections[key] = "\n".join(
            sections[key]
        ).strip()

    return sections


def extract_resume(pdf_path: str) -> dict:
    """
    Extract a resume PDF into a structured JSON-compatible dictionary.

    No LLM is used here.
    """

    pdf_path = Path(pdf_path)

    file_hash = calculate_file_hash(
        str(pdf_path)
    )

    result = {
        "resume_id": file_hash[:16],

        "file": {
            "filename": pdf_path.name,
            "file_hash": file_hash,
            "file_type": "pdf"
        },

        "document": {
            "page_count": 0,
            "status": "success"
        },

        "candidate": {
            "name": None,
            "emails": []
        },

        "skills": [],

        "sections": {},

        "pages": [],

        "full_text": "",

        "error": None
    }

    try:

        document = fitz.open(
            str(pdf_path)
        )

        result["document"]["page_count"] = len(
            document
        )

        all_page_text = []

        for page_number, page in enumerate(
            document,
            start=1
        ):

            text = page.get_text(
                "text"
            ).strip()

            result["pages"].append({
                "page_number": page_number,
                "text": text
            })

            if text:
                all_page_text.append(text)

        document.close()

        full_text = "\n\n".join(
            all_page_text
        )

        result["full_text"] = full_text

        if not full_text.strip():

            result["document"]["status"] = "empty"

            result["error"] = (
                "No readable text found in PDF."
            )

            return result

        # Extract candidate information
        result["candidate"]["name"] = (
            extract_name(full_text)
        )

        result["candidate"]["emails"] = (
            extract_email(full_text)
        )

        # Detect resume sections
        result["sections"] = (
            extract_sections(full_text)
        )

        # Extract skills from the skills section
        skills_text = result["sections"].get(
            "skills",
            ""
        )

        if skills_text:

            raw_skills = re.split(
                r"[,|•\n;]+",
                skills_text
            )

            result["skills"] = [
                skill.strip()
                for skill in raw_skills
                if skill.strip()
            ]

    except Exception as exc:

        result["document"]["status"] = "failed"

        result["error"] = str(exc)

    return result


def extract_resume_folder(folder_path: str) -> list:
    """
    Extract every PDF in a folder.
    """

    folder = Path(folder_path)

    if not folder.exists():

        raise FileNotFoundError(
            f"Folder does not exist: {folder}"
        )

    pdf_files = sorted(
        folder.glob("*.pdf")
    )

    results = []

    for pdf_file in pdf_files:

        print(
            f"Processing: {pdf_file.name}"
        )

        results.append(
            extract_resume(
                str(pdf_file)
            )
        )

    return results