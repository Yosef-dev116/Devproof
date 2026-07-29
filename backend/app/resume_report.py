import json

from openai import OpenAI

OPENAI_MODEL = "gpt-4o-mini"

RESUME_SCHEMA_DESCRIPTION = """
Return ONLY a JSON object with exactly this shape (no markdown, no commentary):

{
  "overall_truthfulness_score": <integer 0-100>,
  "claims": [
    {
      "claim": "<string, the claim as stated on the resume>",
      "verdict": "verified" | "partially_verified" | "unverifiable" | "contradicted",
      "evidence": "<string, 1-3 sentences citing specific GitHub evidence>"
    }
  ],
  "summary": "<string, 2-3 sentences overall assessment>"
}

Extract up to 8 concrete, checkable technical/professional claims from the resume
(skills claimed, years of experience, notable projects, leadership/collaboration
claims). Skip personal details (name, contact info, education dates) - only
claims that GitHub activity could plausibly confirm or contradict.

Base every verdict strictly on the provided GitHub evidence (profile info,
account age, repository list, language frequency, star counts). Use these rules:
- "verified": the evidence directly and clearly supports the claim.
- "partially_verified": the evidence is broadly consistent but doesn't fully confirm
  the specific detail claimed (e.g. resume claims "expert" but evidence only shows
  moderate, recent use).
- "unverifiable": GitHub evidence has nothing relevant either way - do not guess.
- "contradicted": use ONLY when evidence actively conflicts with the claim (e.g.
  "5 years of Python experience" but the account was created under a year ago, or
  claimed expertise in a language that never appears across any repository).

Be strict and specific in "evidence" - name the actual signal used (e.g. "GitHub
account created in March 2025, 8 months before this resume's claimed 5 years of
experience" or "Python appears in 0 of 12 public repositories").
"""


class ResumeReportError(Exception):
    pass


def generate_resume_report(resume_text: str, github_evidence: dict) -> dict:
    client = OpenAI()

    evidence_text = json.dumps(github_evidence, indent=2)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical recruiter cross-referencing a resume "
                        "against a candidate's real GitHub activity to assess how truthful "
                        "its technical claims are. " + RESUME_SCHEMA_DESCRIPTION
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Resume text:\n{resume_text[:6000]}\n\n"
                        f"GitHub evidence:\n{evidence_text}"
                    ),
                },
            ],
        )
    except Exception as error:
        raise ResumeReportError(f"OpenAI request failed: {error}") from error

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as error:
        raise ResumeReportError(f"OpenAI returned invalid JSON: {error}") from error
