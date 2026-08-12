import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_step(step_name: str, script_path: Path, cwd: Path):
    print("\n" + "=" * 70)
    print(f"STEP: {step_name}")
    print(f"Running script: {script_path.relative_to(BASE_DIR)}")
    print("=" * 70)

    result = subprocess.run([sys.executable, str(script_path)], cwd=str(cwd))
    if result.returncode != 0:
        print(f"Warning: Step '{step_name}' exited with return code {result.returncode}")
    else:
        print(f"Step '{step_name}' completed successfully!")

def main():
    print("=" * 70)
    print("PRODAPT HACKATHON -- END-TO-END AI RESUME SCREENING PIPELINE")
    print("=" * 70)

    # 1. Step 1: Resume Processing (PDF text extraction)
    run_step("1. Resume Processing (Extract PDFs)", BASE_DIR / "resume_processing" / "test_parser.py", BASE_DIR / "resume_processing")

    # Step 1b: Groq Resume Structuring (if API key available)
    if os.getenv("GROQ_API_KEY"):
        run_step("1b. Resume Structuring (Groq AI)", BASE_DIR / "resume_processing" / "process_with_groq.py", BASE_DIR / "resume_processing")

    # 2. Step 2: JD Data Processing
    run_step("2. Job Description Processing", BASE_DIR / "matching_service" / "jd_data.py", BASE_DIR)

    # 3. Step 3: Vector Embeddings Conversion
    run_step("3. Vector Embeddings Conversion", BASE_DIR / "matching_service" / "embedding_conversion.py", BASE_DIR)

    # 4. Step 4: Hybrid Matcher & Scoring
    run_step("4. Hybrid Matching Engine", BASE_DIR / "matching_service" / "hybrid_match.py", BASE_DIR)

    # 5. Verification
    results_file = BASE_DIR / "results.json"
    if results_file.exists():
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"Results saved to: {results_file}")
        print("FastAPI Backend & Django Dashboard are ready to serve results.json.")
        print("Run API: uvicorn api.main:app --port 8001")
        print("Run Dashboard: python manage.py runserver 8000")
        print("=" * 70)
    else:
        print("\nPipeline finished but results.json was not created.")

if __name__ == "__main__":
    main()
