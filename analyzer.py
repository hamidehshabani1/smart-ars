import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field


class ResumeAnalysis(BaseModel):
    match_score: int = Field(description="Match percentage from 0 to 100")
    verdict: str = Field(description="Short hiring recommendation (e.g., Strong Match, Moderate Match, Not Recommended)")
    summary: str = Field(description="Concise 2-3 sentence executive summary of the candidate's fit")
    matched_skills: list[str] = Field(description="Key skills and qualifications found in both resume and JD")
    missing_skills: list[str] = Field(description="Important skills required in the JD but missing from the resume")
    interview_questions: list[str] = Field(description="3 to 5 tailored interview questions based on gaps or claims")


def _get_available_models(client: genai.Client) -> list[str]:
    """Starts with gemini-3.8-flash and dynamically adds other available Gemini Flash/Pro models."""
    models = ["gemini-3.8-flash"]
    try:
        for m in client.models.list():
            name = (m.name or "").replace("models/", "")
            if (
                "gemini" in name
                and "embedding" not in name
                and "tts" not in name
                and "image" not in name
                and name not in models
            ):
                # Prioritize flash models before pro models
                if "flash" in name:
                    models.insert(1, name)
                else:
                    models.append(name)
    except Exception:
        pass
    return models[:5]


def analyze_resume(api_key: str, pdf_bytes: bytes, job_description: str, output_lang: str = "Persian") -> ResumeAnalysis:
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert Senior Technical Recruiter and HR Specialist.
    Evaluate the attached resume against the provided Job Description (JD) objectively and strictly.

    Job Description:
    {job_description}

    Instructions:
    1. Analyze skills, experience level, domain relevance, and impact.
    2. Provide the entire response (verdict, summary, skills, and interview questions) in {output_lang}.
    3. Keep technical terms (like Python, SQL, Agile, etc.) in English even when writing in Persian.
    4. Be realistic with the match_score.
    """

    models_to_try = _get_available_models(client)
    last_error = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ResumeAnalysis,
                        temperature=0.2,
                    ),
                )
                return ResumeAnalysis.model_validate_json(response.text)

            except APIError as e:
                last_error = e
                if e.code in (429, 503):
                    time.sleep(2 * (attempt + 1))
                    continue
                if e.code in (400, 404):
                    break  # Skip unsupported model and try the next one
                raise

    raise last_error