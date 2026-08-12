import json
from pathlib import Path

from groq_extractor import GroqResumeExtractor


def main():

    # Input JSON created by test_parser.py
    input_file = Path(
        "output/extracted_resumes.json"
    )

    # Final structured JSON created by Groq
    output_file = Path(
        "output/structured_resumes.json"
    )

    # Check whether input file exists
    if not input_file.exists():

        print(
            "extracted_resumes.json not found."
        )

        print(
            "Run test_parser.py first."
        )

        return

    # -----------------------------------------
    # Load extracted resume JSON
    # -----------------------------------------

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # -----------------------------------------
    # Handle both possible JSON formats
    # -----------------------------------------
    #
    # Format 1:
    #
    # [
    #     {...},
    #     {...}
    # ]
    #
    # Format 2:
    #
    # {
    #     "total_resumes": 3,
    #     "resumes": [
    #         {...},
    #         {...}
    #     ]
    # }
    #
    # -----------------------------------------

    if isinstance(data, list):

        resumes = data

    elif isinstance(data, dict):

        resumes = data.get(
            "resumes",
            []
        )

    else:

        print(
            "Invalid JSON format in extracted_resumes.json."
        )

        return

    # Check whether resumes were found
    if not resumes:

        print(
            "No resumes found in extracted_resumes.json."
        )

        return

    print(
        f"Found {len(resumes)} resume(s)."
    )

    # -----------------------------------------
    # Initialize Groq extractor
    # -----------------------------------------

    try:

        extractor = GroqResumeExtractor()

    except Exception as exc:

        print(
            "\nFailed to initialize Groq:"
        )

        print(exc)

        return

    # -----------------------------------------
    # Process each resume
    # -----------------------------------------

    structured_resumes = []

    for index, resume in enumerate(
        resumes,
        start=1
    ):

        # Get filename safely
        filename = resume.get(
            "file",
            {}
        ).get(
            "filename",
            f"resume_{index}.pdf"
        )

        resume_id = resume.get(
            "resume_id"
        )

        print("\n" + "=" * 60)

        print(
            f"Processing {index}/{len(resumes)}"
        )

        print(
            f"File: {filename}"
        )

        print(
            f"Resume ID: {resume_id}"
        )

        print("=" * 60)

        try:

            # Send extracted resume information to Groq
            structured = extractor.extract(
                resume
            )

            # Make sure important identifiers
            # are preserved
            structured["resume_id"] = resume_id

            structured["filename"] = filename

            structured["status"] = "success"

            structured_resumes.append(
                structured
            )

            print(
                f"Successfully structured: {filename}"
            )

        except Exception as exc:

            print(
                f"Failed: {filename}"
            )

            print(
                f"Error: {exc}"
            )

            # Keep failed resume information
            # instead of stopping the entire batch
            structured_resumes.append({

                "resume_id": resume_id,

                "filename": filename,

                "status": "failed",

                "error": str(exc)

            })

    # -----------------------------------------
    # Create output directory
    # -----------------------------------------

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------
    # Save structured JSON
    # -----------------------------------------

    final_output = {

        "total_resumes": len(
            structured_resumes
        ),

        "successful": sum(
            1
            for resume in structured_resumes
            if resume.get("status") == "success"
        ),

        "failed": sum(
            1
            for resume in structured_resumes
            if resume.get("status") == "failed"
        ),

        "resumes": structured_resumes
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_output,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------
    # Final message
    # -----------------------------------------

    print("\n" + "=" * 60)

    print(
        "GROQ EXTRACTION COMPLETE"
    )

    print("=" * 60)

    print(
        f"Total resumes: "
        f"{final_output['total_resumes']}"
    )

    print(
        f"Successful: "
        f"{final_output['successful']}"
    )

    print(
        f"Failed: "
        f"{final_output['failed']}"
    )

    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()