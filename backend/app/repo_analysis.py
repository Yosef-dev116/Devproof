from backend.app.github_client import fetch_tree_and_readme, fetch_sample_files
from backend.app.analysis import detect_signals
from backend.app.code_quality import select_sample_files, detect_type_safety_signals
from backend.app.ai_report import generate_report


def analyze_repo(owner: str, repo: str, repo_info: dict) -> dict:
    """
    Runs the evidence-gathering + AI report pipeline for a single repository.

    `repo_info` must supply stars/forks/language/description/recent_commit_count/
    default_branch - the shape returned by github_client.fetch_repo_data().

    Raises requests.HTTPError (from the GitHub tree/README fetch) or
    ai_report.AIReportError (from the OpenAI call) on failure - callers
    translate those to whatever response makes sense for their own route.
    """
    file_entries, readme_text = fetch_tree_and_readme(owner, repo, repo_info["default_branch"])

    file_paths = [entry["path"] for entry in file_entries]
    signals = detect_signals(file_paths)

    sample_paths = select_sample_files(file_entries)
    sample_contents = fetch_sample_files(owner, repo, sample_paths)
    type_safety_signals = detect_type_safety_signals(sample_contents)

    evidence = {
        "stars": repo_info["stars"],
        "forks": repo_info["forks"],
        "language": repo_info["language"],
        "description": repo_info["description"],
        "recent_commit_count": repo_info["recent_commit_count"],
        **signals,
        "readme_excerpt": (readme_text or "")[:1500],
        "type_safety_signals": type_safety_signals,
    }

    report = generate_report(evidence)

    return {"report": report, "type_safety_signals": type_safety_signals}
