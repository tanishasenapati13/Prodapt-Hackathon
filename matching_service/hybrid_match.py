import os
import json
import re
from datetime import datetime, timezone

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

RESUME_DIR = "data/resumes"
JD_FILE = "data/jd.json"

FAISS_INDEX = "vector_store/resumes.faiss"
METADATA_FILE = "vector_store/metadata.json"

OUTPUT_FILE = "results.json"

# Hybrid matching weights
SKILL_WEIGHT = 0.60
VECTOR_WEIGHT = 0.40

# Partial skill similarity threshold
PARTIAL_THRESHOLD = 0.70

# Semantic score thresholds
SHORTLIST_THRESHOLD = 75
CONSIDER_THRESHOLD = 60


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def normalize_skill(skill):
    """
    Normalize skill names so that equivalent names
    can be compared more easily.
    """

    skill = skill.lower().strip()

    replacements = {
        "python programming": "python",
        "python development": "python",

        "postgres": "postgresql",
        "postgres db": "postgresql",

        "react.js": "react",
        "reactjs": "react",

        "node.js": "node",
        "nodejs": "node",

        "amazon web services": "aws",

        "google cloud platform": "gcp",

        "machine-learning": "machine learning",
        "ml": "machine learning",

        "natural language processing": "nlp",

        "structured query language": "sql"
    }

    return replacements.get(skill, skill)


def normalize_skills(skills):
    """
    Normalize and remove duplicate skills.
    """

    result = set()

    for skill in skills:
        result.add(normalize_skill(skill))

    return result


def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors.
    """

    a = np.asarray(a)
    b = np.asarray(b)

    denominator = (
        np.linalg.norm(a) *
        np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def load_job_description():

    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd = json.load(f)

    return jd


def load_resumes():

    resumes = {}

    for filename in os.listdir(RESUME_DIR):

        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(
            RESUME_DIR,
            filename
        )

        try:

            with open(filepath, "r", encoding="utf-8") as f:
                resume = json.load(f)

            resume_id = resume.get(
                "resume_id",
                os.path.splitext(filename)[0]
            )

            resumes[resume_id] = resume

        except Exception as e:

            print(
                f"Failed to load {filename}: {e}"
            )

    return resumes


def load_vector_store():

    print("Loading FAISS vector store...")

    index = faiss.read_index(
        FAISS_INDEX
    )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        metadata = json.load(f)

    return index, metadata


# ============================================================
# BUILD JD TEXT
# ============================================================

def build_jd_text(jd):

    required = jd.get(
        "required_skills",
        []
    )

    preferred = jd.get(
        "preferred_skills",
        []
    )

    description = jd.get(
        "description",
        ""
    )

    text = f"""
    Job Title:
    {jd.get("job_title", "")}

    Required Skills:
    {", ".join(required)}

    Preferred Skills:
    {", ".join(preferred)}

    Description:
    {description}
    """

    return text


# ============================================================
# BUILD RESUME TEXT
# ============================================================

def build_resume_text(resume):

    skills = resume.get(
        "skills",
        []
    )

    experience = resume.get(
        "experience",
        []
    )

    projects = resume.get(
        "projects",
        []
    )

    experience_text = ""

    for exp in experience:

        experience_text += (
            f"{exp.get('role', '')}. "
            f"{exp.get('description', '')} "
        )

    project_text = ""

    for project in projects:

        project_text += (
            f"{project.get('name', '')}. "
            f"{project.get('description', '')} "
        )

    return f"""
    Skills:
    {", ".join(skills)}

    Experience:
    {experience_text}

    Projects:
    {project_text}
    """


# ============================================================
# FIND MATCHED / MISSING SKILLS
# ============================================================

def compare_skills(
    resume_skills,
    required_skills,
    preferred_skills
):

    resume_normalized = normalize_skills(
        resume_skills
    )

    required_normalized = normalize_skills(
        required_skills
    )

    preferred_normalized = normalize_skills(
        preferred_skills
    )

    matched = []
    missing = []
    partial = []

    # --------------------------------------------------------
    # Exact matches
    # --------------------------------------------------------

    for skill in required_normalized:

        if skill in resume_normalized:

            matched.append(skill)

        else:

            missing.append(skill)

    # --------------------------------------------------------
    # Semantic matching for missing skills
    # --------------------------------------------------------

    resume_skill_list = list(
        resume_normalized
    )

    if resume_skill_list:

        resume_embeddings = model.encode(
            resume_skill_list,
            normalize_embeddings=True
        )

    else:

        resume_embeddings = []

    final_missing = []

    for skill in missing:

        skill_embedding = model.encode(
            [skill],
            normalize_embeddings=True
        )[0]

        best_similarity = 0
        best_skill = None

        for i, resume_skill in enumerate(
            resume_skill_list
        ):

            similarity = float(
                np.dot(
                    skill_embedding,
                    resume_embeddings[i]
                )
            )

            if similarity > best_similarity:

                best_similarity = similarity
                best_skill = resume_skill

        if best_similarity >= PARTIAL_THRESHOLD:

            partial.append({
                "required_skill": skill,
                "resume_skill": best_skill,
                "similarity": round(
                    best_similarity,
                    3
                )
            })

        else:

            final_missing.append(skill)

    return (
        matched,
        partial,
        final_missing
    )


# ============================================================
# CALCULATE SKILL SCORE
# ============================================================

def calculate_skill_score(
    matched,
    partial,
    required_skills
):

    total_required = len(
        required_skills
    )

    if total_required == 0:
        return 0

    matched_points = len(
        matched
    )

    partial_points = (
        len(partial) * 0.5
    )

    score = (
        matched_points +
        partial_points
    ) / total_required

    return clamp(
        score * 100
    )


# ============================================================
# VECTOR SEARCH
# ============================================================

def calculate_vector_similarity(
    jd,
    resume_id,
    index,
    metadata
):

    jd_text = build_jd_text(jd)

    jd_embedding = model.encode(
        [jd_text],
        normalize_embeddings=True
    )

    # --------------------------------------------------------
    # Find resume inside metadata
    # --------------------------------------------------------

    resume_vector_id = None

    for item in metadata:

        if item["resume_id"] == resume_id:

            resume_vector_id = item["vector_id"]

            break

    if resume_vector_id is None:

        return 0.0

    # --------------------------------------------------------
    # Retrieve vector from FAISS
    # --------------------------------------------------------

    resume_vector = index.reconstruct(
        int(resume_vector_id)
    )

    resume_vector = np.asarray(
        resume_vector
    )

    # --------------------------------------------------------
    # Cosine similarity
    # --------------------------------------------------------

    similarity = cosine_similarity(
        jd_embedding[0],
        resume_vector
    )

    return similarity


# ============================================================
# GENERATE INSIGHTS
# ============================================================

def generate_strengths(
    matched,
    partial
):

    strengths = []

    if matched:

        strengths.append(
            "Strong match across required skills: "
            + ", ".join(matched[:5])
        )

    if partial:

        strengths.append(
            "Has related experience for "
            "some required skills."
        )

    if not strengths:

        strengths.append(
            "Limited direct skill alignment "
            "with the job requirements."
        )

    return strengths


def generate_gaps(
    missing,
    partial
):

    gaps = []

    if missing:

        gaps.append(
            "Missing required skills: "
            + ", ".join(missing[:5])
        )

    if partial:

        gaps.append(
            "Some required skills have only "
            "partial/related matches."
        )

    return gaps


# ============================================================
# HIRING RECOMMENDATION
# ============================================================

def get_recommendation(score):

    if score >= SHORTLIST_THRESHOLD:

        return "Shortlist"

    elif score >= CONSIDER_THRESHOLD:

        return "Consider"

    else:

        return "Reject"


# ============================================================
# MATCH ONE RESUME
# ============================================================

def match_resume(
    resume,
    jd,
    index,
    metadata
):

    resume_id = resume["resume_id"]

    required_skills = jd.get(
        "required_skills",
        []
    )

    preferred_skills = jd.get(
        "preferred_skills",
        []
    )

    resume_skills = resume.get(
        "skills",
        []
    )

    # --------------------------------------------------------
    # Skill matching
    # --------------------------------------------------------

    (
        matched,
        partial,
        missing
    ) = compare_skills(
        resume_skills,
        required_skills,
        preferred_skills
    )

    skill_score = calculate_skill_score(
        matched,
        partial,
        required_skills
    )

    # --------------------------------------------------------
    # Vector matching
    # --------------------------------------------------------

    vector_similarity = (
        calculate_vector_similarity(
            jd,
            resume_id,
            index,
            metadata
        )
    )

    vector_score = (
        vector_similarity * 100
    )

    # --------------------------------------------------------
    # Hybrid score
    # --------------------------------------------------------

    overall_score = (
        SKILL_WEIGHT * skill_score
        +
        VECTOR_WEIGHT * vector_score
    )

    overall_score = round(
        clamp(overall_score),
        2
    )

    # --------------------------------------------------------
    # Generate explanation
    # --------------------------------------------------------

    strengths = generate_strengths(
        matched,
        partial
    )

    gaps = generate_gaps(
        missing,
        partial
    )

    rationale = (
        f"Candidate matches {len(matched)} "
        f"of {len(required_skills)} required skills. "
        f"The hybrid matching score is "
        f"{overall_score}%, combining skill-level "
        f"matching and semantic similarity."
    )

    # --------------------------------------------------------
    # Final dashboard payload
    # --------------------------------------------------------

    result = {

        "resume_id": resume_id,

        "candidate_name": resume.get(
            "candidate_name"
        ),

        "resume_filename": resume.get(
            "resume_filename"
        ),

        "job_description_id": jd.get(
            "job_description_id"
        ),

        "job_title": jd.get(
            "job_title"
        ),

        "status": "scored",

        "overall_match_percentage": overall_score,

        # Internal backend metric
        "vector_similarity_score": round(
            vector_similarity,
            3
        ),

        "analysis": {

            "matched_skills": matched,

            "partial_skills": partial,

            "missing_skills": missing,

            "strengths": strengths,

            "gaps": gaps,

            "ai_rationale": rationale,

            "hiring_recommendation":
                get_recommendation(
                    overall_score
                )
        },

        "processed_at":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nLoading data...")

    jd = load_job_description()

    resumes = load_resumes()

    index, metadata = load_vector_store()

    print(
        f"Loaded {len(resumes)} resumes."
    )

    results = []

    # --------------------------------------------------------
    # Process every resume
    # --------------------------------------------------------

    for resume_id, resume in resumes.items():

        print(
            f"Processing {resume_id}..."
        )

        try:

            result = match_resume(
                resume,
                jd,
                index,
                metadata
            )

            results.append(result)

        except Exception as e:

            print(
                f"Failed {resume_id}: {e}"
            )

            results.append({

                "resume_id": resume_id,

                "candidate_name":
                    resume.get(
                        "candidate_name"
                    ),

                "resume_filename":
                    resume.get(
                        "resume_filename"
                    ),

                "job_description_id":
                    jd.get(
                        "job_description_id"
                    ),

                "status": "failed",

                "error": str(e),

                "processed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            })

    # --------------------------------------------------------
    # Rank candidates
    # --------------------------------------------------------

    scored_results = [
        r for r in results
        if r["status"] == "scored"
    ]

    scored_results.sort(
        key=lambda x:
        x["overall_match_percentage"],
        reverse=True
    )

    for rank, result in enumerate(
        scored_results,
        start=1
    ):

        result["rank"] = rank

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    print(
        f"\nResults saved to {OUTPUT_FILE}"
    )

    print("\nRanking:")

    for result in scored_results:

        print(
            f'{result["rank"]}. '
            f'{result["candidate_name"]} '
            f'→ '
            f'{result["overall_match_percentage"]}%'
        )


if __name__ == "__main__":
    main()