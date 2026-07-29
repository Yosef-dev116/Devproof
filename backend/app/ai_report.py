import json

from openai import OpenAI

OPENAI_MODEL = "gpt-4o-mini"

REPORT_SCHEMA_DESCRIPTION = """
Return ONLY a JSON object with exactly this shape (no markdown, no commentary):

{
  "overall_score": <integer 0-100>,
  "categories": [
    {"name": "Code Organization", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Documentation", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Testing", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "DevOps", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Security", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Collaboration", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Project Maturity", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Role Relevance", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"},
    {"name": "Code Quality & Type Safety (AI Slop)", "score": <integer 0-100>, "comment": "<string, max 15 words>", "details": "<string, 3-5 sentences>"}
  ],
  "strengths": [<string, max 12 words> - exactly 3 items],
  "weaknesses": [<string, max 12 words> - exactly 3 items],
  "recommendations": [<string, max 12 words> - exactly 3 items],
  "learning_roadmap": [<string, max 12 words> - exactly 3 items]
}

Be strict about the word limits and item counts above - keep every "comment" and
list item short and to the point. "details" is the one exception: write 3-5 real
sentences there, not a restatement of "comment".

Base every score, comment, and details on the evidence provided. Reference specific
evidence (e.g. "no tests/ directory found", "README is only 3 lines") rather than
making generic claims - "details" especially must be concrete, not generic filler.
For each category's "details", explain (1) exactly what evidence led to this score,
(2) what specifically is present or missing (name real things: which signal, what
the README does/doesn't cover, what the type-safety numbers show), and (3) one
concrete way to improve that specific category. Never write a "details" that just
repeats "comment" in longer words with no new information.

For "Code Quality & Type Safety (AI Slop)", base the score primarily on the
`type_safety_signals` evidence: a high ratio of type-hinted Python functions,
a high ratio of `.ts`/`.tsx` files over untyped `.js`/`.jsx`, real interface/type
declarations, and low `any` usage all score well. Untyped, `any`-heavy, or
inconsistent code is a sign of careless, low-effort ("AI slop") code generation
and should score poorly, even if the code otherwise runs.
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
            max_tokens=2200,
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
