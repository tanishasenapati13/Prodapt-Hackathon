import os
import json
from datetime import datetime, timezone
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

RESUME_DIR = "resumes" if os.path.exists("resumes") else "data/resumes"
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

def normalize_skills(skills):
    return {normalize_skill(s) for s in skills}

def cosine_similarity(a, b):
    a = np.asarray(a).flatten()
    b = np.asarray(b).flatten()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0

def clamp(val, min_val=0, max_val=100):
    return max(min_val, min(max_val, val))

def load_data():
    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd = json.load(f)

    resumes = []
    if os.path.exists(RESUME_DIR):
        for filename in os.listdir(RESUME_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(RESUME_DIR, filename), "r", encoding="utf-8") as f:
                    resumes.append(json.load(f))

    index = faiss.read_index(FAISS_INDEX_FILE)

    with open(RESUME_METADATA_FILE, "r", encoding="utf-8") as f:
        resume_metadata = json.load(f)

    jd_vector = np.load(JD_VECTOR_FILE)

    return jd, resumes, index, resume_metadata, jd_vector

def compare_skills(resume_skills, required_skills):
    res_norm = normalize_skills(resume_skills)
    req_norm = normalize_skills(required_skills)

    matched = [s for s in req_norm if s in res_norm]
    missing_initial = [s for s in req_norm if s not in res_norm]

    res_skill_list = list(res_norm)
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

def generate_strengths(matched, partial):
    if matched:
        return ["Strong match across required skills: " + ", ".join(matched[:5])]
    if partial:
        return ["Has related experience for some required skills."]
    return ["Limited direct skill alignment with the job requirements."]

def generate_gaps(missing, partial):
    gaps = []
    if missing:
        gaps.append("Missing required skills: " + ", ".join(missing[:5]))
    if partial:
        gaps.append("Some required skills have only partial/related matches.")
    return gaps

def get_recommendation(score):
    if score >= SHORTLIST_THRESHOLD:
        return "Shortlist"
    elif score >= CONSIDER_THRESHOLD:
        return "Consider"
    return "Reject"

def match_single_resume(resume, jd, index, resume_metadata, jd_vector):
    resume_id = resume.get("resume_id")
    req_skills = jd.get("required_skills", [])
    res_skills = resume.get("skills", [])

    matched, partial, missing = compare_skills(res_skills, req_skills)
    skill_score = calculate_skill_score(matched, partial, req_skills)
    vec_sim = get_vector_similarity(resume_id, index, resume_metadata, jd_vector)
    vec_score = vec_sim * 100

    overall_score = round(clamp(SKILL_WEIGHT * skill_score + VECTOR_WEIGHT * vec_score), 2)

    return {
        "resume_id": resume_id,
        "candidate_name": resume.get("candidate_name"),
        "resume_filename": resume.get("resume_filename"),
        "job_description_id": jd.get("job_description_id"),
        "job_title": jd.get("job_title"),
        "status": "scored",
        "overall_match_percentage": overall_score,
        "vector_similarity_score": round(vec_sim, 3),
        "analysis": {
            "matched_skills": matched,
            "partial_skills": partial,
            "missing_skills": missing,
            "strengths": generate_strengths(matched, partial),
            "gaps": generate_gaps(missing, partial),
            "ai_rationale": f"Candidate matches {len(matched)} of {len(req_skills)} required skills. Hybrid match score is {overall_score}%.",
            "hiring_recommendation": get_recommendation(overall_score)
        },
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

def main():
    print("Loading pre-processed data & vectors...")
    jd, resumes, index, resume_metadata, jd_vector = load_data()
    print(f"Loaded {len(resumes)} resumes and pre-computed FAISS vector index.")

    results = []
    for resume in resumes:
        resume_id = resume.get("resume_id")
        try:
            results.append(match_single_resume(resume, jd, index, resume_metadata, jd_vector))
        except Exception as e:
            results.append({
                "resume_id": resume_id,
                "candidate_name": resume.get("candidate_name"),
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
        print(f"{item['rank']}. {item['candidate_name']} → {item['overall_match_percentage']}% ({item['analysis']['hiring_recommendation']})")

if __name__ == "__main__":
    main()