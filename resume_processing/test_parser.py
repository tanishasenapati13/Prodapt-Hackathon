import json
from pathlib import Path
import os
import sys

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_parser import extract_resume_folder

def main():
    base_dir = Path(__file__).resolve().parent.parent
    
    # Priority check for common resumes folder
    if (base_dir / "resumes").exists() and list((base_dir / "resumes").glob("*.pdf")):
        resume_folder = base_dir / "resumes"
    elif (base_dir / "resume_processing" / "test_resumes").exists():
        resume_folder = base_dir / "resume_processing" / "test_resumes"
    else:
        resume_folder = Path("resumes")

    print(f"Reading resume PDFs from: {resume_folder}")
    results = extract_resume_folder(str(resume_folder))

    output_folder = base_dir / "output"
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / "extracted_resumes.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    print("\n==============================")
    print("RESUME EXTRACTION COMPLETE")
    print("==============================")
    print(f"Total resumes: {len(results)}")
    print(f"JSON saved to: {output_file}")

    for result in results:
        status = result.get("document", {}).get("status", "unknown")
        filename = result.get("file", {}).get("filename", "resume.pdf")
        print(f" -> {filename}: {status}")

if __name__ == "__main__":
    main()