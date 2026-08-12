import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class GroqResumeExtractor:

    def __init__(
        self,
        model="llama-3.3-70b-versatile"
    ):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set in .env"
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = model

    def build_prompt(self, resume_data):

        return f"""
You are a resume information extraction system.

You will receive JSON containing text extracted from a PDF resume.

Your task is to analyze the extracted resume information and return
ONE detailed, structured JSON object.

IMPORTANT RULES:

1. Use ONLY information explicitly present in the provided resume.
2. Do NOT hallucinate, assume, or infer information that is not present.
3. Do NOT add phone numbers.
4. Do NOT perform job matching.
5. Do NOT calculate match percentages.
6. Do NOT provide hiring recommendations.
7. Do NOT evaluate whether the candidate is suitable for any job.
8. Preserve important technical and professional details.
9. If a single-value field is not available, use null.
10. If a list field has no information, use [].
11. Do not duplicate the same information unnecessarily.
12. Keep technologies and skills exactly as mentioned whenever possible.
13. Return ONLY valid JSON.
14. Do NOT use Markdown.
15. Do NOT wrap the response in ```json or ```.

EXTRACT THE FOLLOWING:

1. Candidate information
   - name
   - email

2. Professional summary/profile

3. Skills

   Put ALL skills into ONE single array.

   Do NOT categorize skills into programming languages,
   frameworks, databases, cloud, etc.

   Include all explicitly mentioned technical skills, such as:
   - programming languages
   - frameworks
   - libraries
   - databases
   - cloud technologies
   - DevOps technologies
   - developer tools
   - AI/ML technologies
   - web technologies
   - APIs
   - software engineering concepts
   - other technical skills

   Example:

   "skills": [
       "Python",
       "Java",
       "FastAPI",
       "PostgreSQL",
       "Docker",
       "AWS",
       "Machine Learning",
       "Git"
   ]

4. Work experience

   For every work experience entry, extract:
   - company
   - role
   - location
   - start date
   - end date
   - duration
   - responsibilities
   - technologies used

5. Education

   For every education entry, extract:
   - degree
   - field of study
   - institution
   - location
   - start year
   - end year
   - CGPA/grade

6. Projects

   For every project, extract:
   - project name
   - description
   - technologies used
   - responsibilities/contributions
   - outcomes/results

7. Certifications

   Extract:
   - certification name
   - issuing organization
   - date/year

8. Achievements

   Extract all explicitly mentioned academic,
   technical, professional, competition, or other achievements.

9. Publications / Research

   Extract publications, research papers, patents,
   conferences, or research work if explicitly mentioned.

10. Languages

    Extract languages explicitly mentioned as spoken,
    written, or known by the candidate.

11. Relevant coursework

    Extract coursework explicitly mentioned in the resume.

12. Professional links

    Extract:
    - LinkedIn
    - GitHub
    - Portfolio
    - Other relevant URLs

IMPORTANT EXTRACTION RULES:

- Do not convert responsibilities into skills unless the
  technology/skill is explicitly mentioned.
- Do not convert company names into skills.
- Do not convert project names into skills unless the project
  name itself explicitly contains a technology.
- Do not create experience entries from projects.
- Do not create education entries from assumptions.
- Do not guess dates.
- Do not guess job titles.
- Do not guess technologies.
- Preserve multiple experience, education, and project entries.
- If there are multiple resumes in the input, process them separately.
- Keep the resume_id and filename from the input.
- Preserve the page_count from the input.

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "resume_id": "",
    "filename": "",
    "page_count": 0,

    "candidate": {{
        "name": null,
        "email": null
    }},

    "summary": null,

    "skills": [],

    "experience": [
        {{
            "company": "",
            "role": "",
            "location": null,
            "start_date": null,
            "end_date": null,
            "duration": null,
            "responsibilities": [],
            "technologies_used": []
        }}
    ],

    "education": [
        {{
            "degree": "",
            "field_of_study": null,
            "institution": "",
            "location": null,
            "start_year": null,
            "end_year": null,
            "grade_or_cgpa": null
        }}
    ],

    "projects": [
        {{
            "project_name": "",
            "description": "",
            "technologies_used": [],
            "responsibilities": [],
            "outcomes": []
        }}
    ],

    "certifications": [],

    "achievements": [],

    "publications": [],

    "languages": [],

    "coursework": [],

    "links": {{
        "linkedin": null,
        "github": null,
        "portfolio": null,
        "other": []
    }},

    "status": "success"
}}

Here is the extracted resume JSON:



{json.dumps(resume_data, indent=2, ensure_ascii=False)}
"""

    def clean_response(self, response_text):

        response_text = response_text.strip()

        # Remove Markdown code fences if the model
        # accidentally returns them.
        if response_text.startswith("```"):

            response_text = re.sub(
                r"^```(?:json)?\s*",
                "",
                response_text,
                flags=re.IGNORECASE
            )

            response_text = re.sub(
                r"\s*```$",
                "",
                response_text
            )

        return response_text.strip()

    def extract(self, resume_data):

        prompt = self.build_prompt(
            resume_data
        )

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured information "
                        "from resumes. Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0,

            max_tokens=4000
        )

        content = response.choices[0].message.content

        content = self.clean_response(
            content
        )

        try:

            return json.loads(content)

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Groq returned invalid JSON: {exc}\n\n"
                f"Response:\n{content}"
            )