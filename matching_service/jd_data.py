import os
import json
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_JD_FILE = "data/raw_jd.txt"
OUTPUT_JD_FILE = "data/jd.json"

GROQ_MODEL = "llama-3.3-70b-versatile"


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ============================================================
# READ RAW JD
# ============================================================

def load_raw_jd():

    return """
    We are looking for a Data Scientist to analyze large amounts of raw information to find patterns that will help improve our company. We will rely on you to build data products to extract valuable business insights.

In this role, you should be highly analytical with a knack for analysis, math and statistics. Critical thinking and problem-solving skills are essential for interpreting data. We also want to see a passion for machine-learning and research.

Your goal will be to help our company analyze trends to make better decisions.
Responsibilities

    Identify valuable data sources and automate collection processes
    Undertake preprocessing of structured and unstructured data
    Analyze large amounts of information to discover trends and patterns
    Build predictive models and machine-learning algorithms
    Combine models through ensemble modeling
    Present information using data visualization techniques
    Propose solutions and strategies to business challenges
    Collaborate with engineering and product development teams

Requirements and skills

    Proven experience as a Data Scientist or Data Analyst
    Experience in data mining
    Understanding of machine-learning and operations research
    Knowledge of R, SQL and Python; familiarity with Scala, Java or C++ is an asset
    Experience using business intelligence tools (e.g. Tableau) and data frameworks (e.g. Hadoop)
    Analytical mind and business acumen
    Strong math skills (e.g. statistics, algebra)
    Problem-solving aptitude
    Excellent communication and presentation skills
    BSc/BA in Computer Science, Engineering or relevant field; graduate degree in Data Science or other quantitative field is preferred

"""



# ============================================================
# EXTRACT JSON FROM LLM RESPONSE
# ============================================================

def extract_json(response_text):

    response_text = response_text.strip()

    # Remove markdown code fences if present
    response_text = re.sub(
        r"```json\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = re.sub(
        r"```\s*$",
        "",
        response_text
    )

    # Find JSON object
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "No valid JSON object found in LLM response."
        )

    json_text = response_text[
        start:end + 1
    ]

    return json.loads(json_text)


# ============================================================
# EXTRACT JD INFORMATION USING GROQ
# ============================================================

def extract_jd_information(raw_jd):

    prompt = f"""
You are an expert recruitment information extraction system.

Analyze the following job description and convert it into
structured JSON.

IMPORTANT:
- Do not invent information.
- If something is not present, use an empty list or null.
- Separate mandatory/required skills from preferred/nice-to-have skills.
- Extract individual technical skills rather than broad categories.
- Normalize obvious aliases where appropriate.
  Example:
    PostgreSQL -> PostgreSQL
    Postgres -> PostgreSQL
    React.js -> React
    Node.js -> Node.js
- Do not treat generic words such as "teamwork", "communication",
  or "problem solving" as technical skills.
- Preserve the original job description in the output.

Return ONLY valid JSON.

Required JSON structure:

{{
    "job_title": "",
    "department": "",
    "seniority": "",
    "location": "",
    "employment_type": "",

    "required_skills": [],

    "preferred_skills": [],

    "required_tools": [],

    "preferred_tools": [],

    "required_qualifications": [],

    "preferred_qualifications": [],

    "required_experience_years": null,

    "responsibilities": [],

    "soft_skills": [],

    "domain_keywords": [],

    "education": [],

    "certifications": [],

    "description": ""
}}

JOB DESCRIPTION:

{raw_jd}
"""

    print("Sending JD to Groq...")

    response = client.chat.completions.create(

        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured recruitment "
                    "information from job descriptions."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0,

        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content

    return extract_json(content)


# ============================================================
# NORMALIZE SKILLS
# ============================================================

def normalize_skill(skill):

    skill = skill.strip()

    replacements = {

        "python programming": "Python",

        "python development": "Python",

        "postgres": "PostgreSQL",

        "postgres db": "PostgreSQL",

        "react.js": "React",

        "reactjs": "React",

        "nodejs": "Node.js",

        "node.js": "Node.js",

        "amazon web services": "AWS",

        "google cloud platform": "GCP",

        "microsoft azure": "Azure",

        "machine-learning": "Machine Learning",

        "ml": "Machine Learning",

        "natural language processing":
            "NLP",

        "structured query language":
            "SQL"
    }

    key = skill.lower().strip()

    return replacements.get(
        key,
        skill
    )


def normalize_skill_list(skills):

    normalized = []

    seen = set()

    for skill in skills:

        skill = normalize_skill(skill)

        key = skill.lower()

        if key not in seen:

            normalized.append(skill)

            seen.add(key)

    return normalized


# ============================================================
# CLEAN EXTRACTED DATA
# ============================================================

def clean_jd_data(jd_data, raw_jd):

    list_fields = [

        "required_skills",
        "preferred_skills",
        "required_tools",
        "preferred_tools",
        "required_qualifications",
        "preferred_qualifications",
        "responsibilities",
        "soft_skills",
        "domain_keywords",
        "education",
        "certifications"
    ]

    for field in list_fields:

        value = jd_data.get(
            field,
            []
        )

        if value is None:

            value = []

        if not isinstance(value, list):

            value = [value]

        # Remove empty values
        value = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        jd_data[field] = value

    # Normalize skills
    jd_data["required_skills"] = (
        normalize_skill_list(
            jd_data["required_skills"]
        )
    )

    jd_data["preferred_skills"] = (
        normalize_skill_list(
            jd_data["preferred_skills"]
        )
    )

    jd_data["required_tools"] = (
        normalize_skill_list(
            jd_data["required_tools"]
        )
    )

    jd_data["preferred_tools"] = (
        normalize_skill_list(
            jd_data["preferred_tools"]
        )
    )

    # Preserve original JD
    jd_data["description"] = raw_jd

    return jd_data


# ============================================================
# CREATE FINAL JD OBJECT
# ============================================================

def create_final_jd(jd_data):

    final_jd = {

        "job_description_id":
            "jd_" +
            datetime.now(
                timezone.utc
            ).strftime("%Y%m%d%H%M%S"),

        "job_title":
            jd_data.get(
                "job_title"
            ),

        "department":
            jd_data.get(
                "department"
            ),

        "seniority":
            jd_data.get(
                "seniority"
            ),

        "location":
            jd_data.get(
                "location"
            ),

        "employment_type":
            jd_data.get(
                "employment_type"
            ),

        "required_skills":
            jd_data.get(
                "required_skills",
                []
            ),

        "preferred_skills":
            jd_data.get(
                "preferred_skills",
                []
            ),

        "required_tools":
            jd_data.get(
                "required_tools",
                []
            ),

        "preferred_tools":
            jd_data.get(
                "preferred_tools",
                []
            ),

        "required_qualifications":
            jd_data.get(
                "required_qualifications",
                []
            ),

        "preferred_qualifications":
            jd_data.get(
                "preferred_qualifications",
                []
            ),

        "required_experience_years":
            jd_data.get(
                "required_experience_years"
            ),

        "responsibilities":
            jd_data.get(
                "responsibilities",
                []
            ),

        "soft_skills":
            jd_data.get(
                "soft_skills",
                []
            ),

        "domain_keywords":
            jd_data.get(
                "domain_keywords",
                []
            ),

        "education":
            jd_data.get(
                "education",
                []
            ),

        "certifications":
            jd_data.get(
                "certifications",
                []
            ),

        "description":
            jd_data.get(
                "description",
                ""
            ),

        "processed_at":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    return final_jd


# ============================================================
# SAVE JD
# ============================================================

def save_jd(jd):

    os.makedirs(
        os.path.dirname(
            OUTPUT_JD_FILE
        ),
        exist_ok=True
    )

    with open(
        OUTPUT_JD_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            jd,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nJD saved to: {OUTPUT_JD_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Loading raw JD...")

    raw_jd = load_raw_jd()

    if not raw_jd.strip():

        raise ValueError(
            "Job description is empty."
        )

    print("Extracting JD information...")

    extracted_data = (
        extract_jd_information(
            raw_jd
        )
    )

    print("Cleaning extracted data...")

    cleaned_data = clean_jd_data(
        extracted_data,
        raw_jd
    )

    final_jd = create_final_jd(
        cleaned_data
    )

    save_jd(final_jd)

    print("\nExtracted information:")

    print(
        "\nRequired skills:"
    )

    for skill in final_jd[
        "required_skills"
    ]:

        print(f"  ✓ {skill}")

    print(
        "\nPreferred skills:"
    )

    for skill in final_jd[
        "preferred_skills"
    ]:

        print(f"  • {skill}")

    print(
        "\nRequired experience:",
        final_jd[
            "required_experience_years"
        ]
    )


if __name__ == "__main__":
    main()