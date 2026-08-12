import os
import json
import re
from datetime import datetime, timezone
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

JD_FILE = "data/jd.json"
FAISS_INDEX_FILE = "vector_store/resumes.faiss"
RESUME_METADATA_FILE = "vector_store/resume_metadata.json"
JD_VECTOR_FILE = "vector_store/jd_vector.npy"
OUTPUT_FILE = "results.json"

SKILL_WEIGHT = 0.60
VECTOR_WEIGHT = 0.40
PARTIAL_THRESHOLD = 0.70
SHORTLIST_THRESHOLD = 75
CONSIDER_THRESHOLD = 60

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def normalize_skill(skill):
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

def extract_resume_skill_set(resume):
    combined_tokens = set()

    for s in resume.get("skills", []):
        s_str = str(s).strip()
        if s_str:
            combined_tokens.add(normalize_skill(s_str))

    for exp in resume.get("experience", []):
        for tech in exp.get("technologies_used", []):
            if tech:
                combined_tokens.add(normalize_skill(str(tech).strip()))

    for proj in resume.get("projects", []):
        for tech in proj.get("technologies_used", []):
            if tech:
                combined_tokens.add(normalize_skill(str(tech).strip()))

    text_content = resume.get("full_text") or resume_to_text(resume)
    if text_content:
        text_lower = text_content.lower()
        common_tech_skills = [
            "python", "java", "c++", "c", "javascript", "typescript", "react", "node", "fastapi",
            "django", "flask", "sql", "postgresql", "mysql", "mongodb", "redis", "docker",
            "kubernetes", "aws", "azure", "gcp", "git", "github", "ci/cd", "linux", "rest api",
            "rest apis", "microservices", "pytorch", "tensorflow", "pandas", "numpy", "scikit-learn",
            "machine learning", "nlp", "langchain", "tableau", "hadoop", "r", "cybersecurity",
            "blockchain", "streamlit", "opencv", "swiftui", "flutter", "firebase"
        ]
        for skill in common_tech_skills:
            if re.search(rf'\b{re.escape(skill)}\b', text_lower):
                combined_tokens.add(normalize_skill(skill))

    return combined_tokens

def cosine_similarity(a, b):
    a = np.asarray(a).flatten()
    b = np.asarray(b).flatten()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0

def clamp(val, min_val=0, max_val=100):
    return max(min_val, min(max_val, val))

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

def load_data():
    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd = json.load(f)

    resumes = load_resumes()
    index = faiss.read_index(FAISS_INDEX_FILE)

    with open(RESUME_METADATA_FILE, "r", encoding="utf-8") as f:
        resume_metadata = json.load(f)

    jd_vector = np.load(JD_VECTOR_FILE)

    return jd, resumes, index, resume_metadata, jd_vector

def compare_skills(resume_skill_set, required_skills):
    req_norm = [normalize_skill(s) for s in required_skills]

    matched = [s for s in req_norm if s in resume_skill_set]
    missing_initial = [s for s in req_norm if s not in resume_skill_set]

    res_skill_list = list(resume_skill_set)
    res_embeddings = model.encode(res_skill_list, normalize_embeddings=True) if res_skill_list else []

    partial = []
    final_missing = []

    for skill in missing_initial:
        skill_emb = model.encode([skill], normalize_embeddings=True)[0]
        best_sim = 0.0
        best_skill = None

        for i, res_skill in enumerate(res_skill_list):
            sim = float(np.dot(skill_emb, res_embeddings[i]))
            if sim > best_sim:
                best_sim = sim
                best_skill = res_skill

        if best_sim >= PARTIAL_THRESHOLD:
            partial.append({
                "required_skill": skill,
                "resume_skill": best_skill,
                "similarity": round(best_sim, 3)
            })
        else:
            final_missing.append(skill)

    return matched, partial, final_missing

def calculate_skill_score(matched, partial, required_skills):
    if not required_skills:
        return 0.0
    points = len(matched) + (len(partial) * 0.5)
    return clamp((points / len(required_skills)) * 100)

def get_vector_similarity(resume_id, index, resume_metadata, jd_vector):
    vec_id = None
    for item in resume_metadata:
        if item.get("resume_id") == resume_id:
            vec_id = item.get("vector_id")
            break

    if vec_id is None:
        return 0.0

    resume_vec = index.reconstruct(int(vec_id))
    return cosine_similarity(jd_vector, resume_vec)

def get_recommendation(score):
    if score >= SHORTLIST_THRESHOLD:
        return "Shortlist"
    elif score >= CONSIDER_THRESHOLD:
        return "Consider"
    return "Reject"

def match_single_resume(resume, jd, index, resume_metadata, jd_vector):
    resume_id = resume.get("resume_id")

    cand = resume.get("candidate") or {}
    candidate_name = cand.get("name") or resume.get("candidate_name") or "Candidate"
    email = cand.get("email") or (cand.get("emails") or [""])[0] or resume.get("email") or resume.get("candidate_email") or ""
    filename = resume.get("filename") or resume.get("file", {}).get("filename") or resume.get("resume_filename") or f"{resume_id}.pdf"

    req_skills = jd.get("required_skills", [])
    resume_skill_set = extract_resume_skill_set(resume)

    matched, partial, missing = compare_skills(resume_skill_set, req_skills)
    skill_score = calculate_skill_score(matched, partial, req_skills)
    vec_sim = get_vector_similarity(resume_id, index, resume_metadata, jd_vector)
    vec_score = vec_sim * 100

    overall_score = round(clamp(SKILL_WEIGHT * skill_score + VECTOR_WEIGHT * vec_score), 2)

    return {
        "resume_id": resume_id,
        "candidate_name": candidate_name,
        "email": email,
        "resume_filename": filename,
        "job_description_id": jd.get("job_description_id"),
        "job_title": jd.get("job_title"),
        "status": "scored",
        "overall_match_percentage": overall_score,
        "vector_similarity_score": round(vec_sim, 3),
        "analysis": {
            "matched_skills": matched,
            "partial_skills": partial,
            "missing_skills": missing,
            "strengths": matched,
            "gaps": missing,
            "ai_rationale": f"Candidate matches {len(matched)} of {len(req_skills)} required skills. Hybrid match score is {overall_score}%.",
            "hiring_recommendation": get_recommendation(overall_score)
        },
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

def main():
    print("Loading pre-processed data & vectors...")
    jd, resumes, index, resume_metadata, jd_vector = load_data()
    print(f"Loaded {len(resumes)} resumes from updated extracted schema and pre-computed FAISS vector index.")

    results = []
    for resume in resumes:
        resume_id = resume.get("resume_id")
        try:
            results.append(match_single_resume(resume, jd, index, resume_metadata, jd_vector))
        except Exception as e:
            cand = resume.get("candidate") or {}
            results.append({
                "resume_id": resume_id,
                "candidate_name": cand.get("name") or resume.get("candidate_name"),
                "email": cand.get("email") or (cand.get("emails") or [""])[0] or resume.get("email") or "",
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.now(timezone.utc).isoformat()
            })

    scored = [r for r in results if r["status"] == "scored"]
    scored.sort(key=lambda x: x["overall_match_percentage"], reverse=True)

    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Matching complete. Results saved to {OUTPUT_FILE}")
    print("\nCandidate Rankings:")
    for item in scored:
        print(f"{item['rank']}. {item['candidate_name']} ({item['email']}) -> {item['overall_match_percentage']}% ({item['analysis']['hiring_recommendation']})")

if __name__ == "__main__":
    main()