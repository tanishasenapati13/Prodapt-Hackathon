from pdf_parser import extract_resume_folder
import json
from pathlib import Path


def main():

    # Folder containing all resume PDFs
    resume_folder = "test_resumes"

    # Extract all resumes
    results = extract_resume_folder(resume_folder)

    # Create output folder
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    # Save structured JSON
    output_file = output_folder / "extracted_resumes.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n==============================")
    print("RESUME EXTRACTION COMPLETE")
    print("==============================")

    print(f"Total resumes: {len(results)}")
    print(f"JSON saved to: {output_file}")

    for result in results:
        print(
            f"\n{result['file']['filename']} "
            f"-> {result['document']['status']}"
        )


if __name__ == "__main__":
    main()