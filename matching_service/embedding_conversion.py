import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

JD_FILE = "data/jd.json"
VECTOR_DIR = "vector_store"

RESUME_INDEX_FILE = os.path.join(VECTOR_DIR, "resumes.faiss")
RESUME_METADATA_FILE = os.path.join(VECTOR_DIR, "resume_metadata.json")
JD_VECTOR_FILE = os.path.join(VECTOR_DIR, "jd_vector.npy")
JD_METADATA_FILE = os.path.join(VECTOR_DIR, "jd_metadata.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print("Embedding model loaded.")

def load_resumes():
    possible_paths = [
        "output/extracted_resumes.json",
        "data/extracted_resumes.json",
        "extracted_resumes.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "resumes" in data:
                    return data["resumes"]
                elif isinstance(data, list):
                    return data

    resumes = []
    resume_dir = "resumes" if os.path.exists("resumes") else "data/resumes"
    if os.path.exists(resume_dir):
        for filename in os.listdir(resume_dir):
            if filename.endswith(".json"):
                with open(os.path.join(resume_dir, filename), "r", encoding="utf-8") as f:
                    resumes.append(json.load(f))
    return resumes

def resume_to_text(resume):
    if resume.get("full_text"):
        return resume["full_text"]

    parts = []
    cand = resume.get("candidate") or {}
    cand_name = cand.get("name") or resume.get("candidate_name") or ""
    if cand_name:
        parts.append(f"Candidate: {cand_name}")

    summary = resume.get("summary")
    if summary:
        parts.append(f"Summary: {summary}")

    skills = resume.get("skills", [])
    if skills:
        parts.append("Skills: " + ", ".join(str(s) for s in skills if s))

    experience = resume.get("experience", [])
    for exp in experience:
        role = exp.get("role", "")
        company = exp.get("company", "")
        resps = " ".join(exp.get("responsibilities", []))
        techs = ", ".join(exp.get("technologies_used", []))
        parts.append(f"Experience: {role} at {company}. {resps} Technologies: {techs}")

    projects = resume.get("projects", [])
    for proj in projects:
        pname = proj.get("project_name") or proj.get("name") or ""
        pdesc = proj.get("description", "")
        ptechs = ", ".join(proj.get("technologies_used", []))
        parts.append(f"Project: {pname}. {pdesc} Technologies: {ptechs}")

    education = resume.get("education", [])
    for edu in education:
        degree = edu.get("degree", "")
        inst = edu.get("institution", "")
        parts.append(f"Education: {degree} from {inst}")

    return "\n".join(parts)

def jd_to_text(jd):
    parts = []
    parts.append(f"Job Title: {jd.get('job_title', '')}")

    required_skills = jd.get("required_skills", [])
    if required_skills:
        parts.append("Required Skills: " + ", ".join(required_skills))

    preferred_skills = jd.get("preferred_skills", [])
    if preferred_skills:
        parts.append("Preferred Skills: " + ", ".join(preferred_skills))

    required_tools = jd.get("required_tools", [])
    if required_tools:
        parts.append("Required Tools: " + ", ".join(required_tools))

    preferred_tools = jd.get("preferred_tools", [])
    if preferred_tools:
        parts.append("Preferred Tools: " + ", ".join(preferred_tools))

    qualifications = jd.get("required_qualifications", [])
    if qualifications:
        parts.append("Required Qualifications: " + ", ".join(str(x) for x in qualifications))

    experience_years = jd.get("required_experience_years")
    if experience_years is not None:
        parts.append(f"Required Experience: {experience_years} years")

    responsibilities = jd.get("responsibilities", [])
    if responsibilities:
        parts.append("Responsibilities:\n" + "\n".join(f"- {x}" for x in responsibilities))

    keywords = jd.get("domain_keywords", [])
    if keywords:
        parts.append("Domain Keywords: " + ", ".join(keywords))

    education = jd.get("education", [])
    if education:
        parts.append("Education: " + ", ".join(str(x) for x in education))

    description = jd.get("description", "")
    if description:
        parts.append("Job Description:\n" + description)

    return "\n".join(parts)

def create_resume_vector_store(resumes):
    print(f"\nCreating embeddings for {len(resumes)} resumes...")
    resume_texts = []
    metadata = []

    for vector_id, resume in enumerate(resumes):
        text = resume_to_text(resume)
        resume_texts.append(text)

        resume_id = resume.get("resume_id")
        cand = resume.get("candidate") or {}
        candidate_name = cand.get("name") or resume.get("candidate_name") or ""
        email = cand.get("email") or (cand.get("emails") or [""])[0] or resume.get("email") or resume.get("candidate_email") or ""
        filename = resume.get("filename") or resume.get("file", {}).get("filename") or resume.get("resume_filename") or f"{resume_id}.pdf"

        metadata.append({
            "vector_id": vector_id,
            "resume_id": resume_id,
            "candidate_name": candidate_name,
            "email": email,
            "resume_filename": filename
        })

    embeddings = model.encode(resume_texts, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.asarray(embeddings, dtype="float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    os.makedirs(VECTOR_DIR, exist_ok=True)
    faiss.write_index(index, RESUME_INDEX_FILE)

    with open(RESUME_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Resume FAISS index saved to: {RESUME_INDEX_FILE}")
    print(f"Resume metadata saved to: {RESUME_METADATA_FILE}")
    print(f"Vector dimension: {dimension}")
    print(f"Vectors stored: {index.ntotal}")

def create_jd_vector(jd):
    print("\nCreating JD embedding...")
    jd_text = jd_to_text(jd)
    embedding = model.encode([jd_text], normalize_embeddings=True)
    embedding = np.asarray(embedding, dtype="float32")

    np.save(JD_VECTOR_FILE, embedding)

    jd_metadata = {
        "job_description_id": jd.get("job_description_id"),
        "job_title": jd.get("job_title"),
        "model": MODEL_NAME,
        "dimension": int(embedding.shape[1])
    }

    with open(JD_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(jd_metadata, f, indent=2)

    print(f"JD vector saved to: {JD_VECTOR_FILE}")
    print(f"JD metadata saved to: {JD_METADATA_FILE}")

def main():
    os.makedirs(VECTOR_DIR, exist_ok=True)
    print("\nLoading resumes...")
    resumes = load_resumes()
    if not resumes:
        raise ValueError("No extracted resumes JSON found.")
    print(f"Found {len(resumes)} resumes.")

    create_resume_vector_store(resumes)

    print("\nLoading JD...")
    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd = json.load(f)

    create_jd_vector(jd)

if __name__ == "__main__":
    main()
