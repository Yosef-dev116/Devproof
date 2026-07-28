import json

from openai import OpenAI

OPENAI_MODEL = "gpt-4o-mini"

REPORT_SCHEMA_DESCRIPTION = """
Return ONLY a JSON object with exactly this shape (no markdown, no commentary):

{
  "overall_score": <integer 0-100>,
  "categories": [
    {"name": "Code Organization", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Documentation", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Testing", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "DevOps", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Security", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Collaboration", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Project Maturity", "score": <integer 0-100>, "comment": "<string, max 15 words>"},
    {"name": "Role Relevance", "score": <integer 0-100>, "comment": "<string, max 15 words>"}
  ],
  "strengths": [<string, max 12 words> - exactly 3 items],
  "weaknesses": [<string, max 12 words> - exactly 3 items],
  "recommendations": [<string, max 12 words> - exactly 3 items],
  "learning_roadmap": [<string, max 12 words> - exactly 3 items]
}

Be strict about the word limits and item counts above - keep every string short and to the point.

Base every score and comment on the evidence provided. Reference specific evidence
(e.g. "no tests/ directory found", "README is only 3 lines") in comments/weaknesses
rather than making generic claims.
"""


class AIReportError(Exception):
    pass


def generate_report(evidence: dict) -> dict:
    client = OpenAI()

    evidence_text = json.dumps(evidence, indent=2)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            max_tokens=900,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software engineering reviewer producing an "
                        "evidence-based engineering readiness report for a GitHub repository. "
                        + REPORT_SCHEMA_DESCRIPTION
                    ),
                },
                {
                    "role": "user",
                    "content": f"Evidence collected about the repository:\n{evidence_text}",
                },
            ],
        )
    except Exception as error:
        raise AIReportError(f"OpenAI request failed: {error}") from error

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as error:
        raise AIReportError(f"OpenAI returned invalid JSON: {error}") from error
