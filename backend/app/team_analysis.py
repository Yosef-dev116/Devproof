def aggregate_contributors(contributors_by_repo: dict[str, list[dict]]) -> list[dict]:
    totals: dict[str, dict] = {}
    for repo_name, contributors in contributors_by_repo.items():
        for contributor in contributors:
            login = contributor["login"]
            entry = totals.setdefault(
                login,
                {
                    "login": login,
                    "avatar_url": contributor.get("avatar_url"),
                    "total_commits": 0,
                    "repositories": [],
                },
            )
            entry["total_commits"] += contributor["contributions"]
            entry["repositories"].append(repo_name)

    return sorted(totals.values(), key=lambda entry: entry["total_commits"], reverse=True)


def select_top_contributors(aggregated_contributors: list[dict], limit: int) -> list[dict]:
    return sorted(aggregated_contributors, key=lambda entry: entry["total_commits"], reverse=True)[:limit]


def find_meaningful_contributions(
    login: str, contributors_by_repo: dict[str, list[dict]], min_commits: int
) -> list[str]:
    return [
        repo_name
        for repo_name, contributors in contributors_by_repo.items()
        for contributor in contributors
        if contributor["login"] == login and contributor["contributions"] >= min_commits
    ]


def select_repos_to_analyze(contributor_repo_map: dict[str, list[str]], max_repos: int) -> list[str]:
    """Dedupe repos referenced by multiple contributors, capped, most-referenced-first."""
    repo_counts: dict[str, int] = {}
    for repo_names in contributor_repo_map.values():
        for repo_name in repo_names:
            repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1

    ranked = sorted(repo_counts.items(), key=lambda item: item[1], reverse=True)
    return [repo_name for repo_name, _ in ranked[:max_repos]]


def _category_score(report: dict, category_name: str) -> int | None:
    for category in report["categories"]:
        if category["name"] == category_name:
            return category["score"]
    return None


def _type_safety_ratio(type_safety_signals: dict) -> int | None:
    total_units = type_safety_signals["python_functions_found"] + type_safety_signals["js_ts_files_found"]
    if total_units == 0:
        return None
    typed_units = (
        type_safety_signals["python_functions_with_type_hints"] + type_safety_signals["typed_ts_files_found"]
    )
    return round(100 * typed_units / total_units)


def _dedupe_capped(items: list[str], cap: int) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
        if len(deduped) >= cap:
            break
    return deduped


def _build_risk_flags(testing_score: int | None, average_type_safety: int | None, analyzed_repo_count: int) -> list[str]:
    flags = []
    if testing_score is not None and testing_score < 50:
        flags.append(f"Low testing coverage signal across analyzed repositories (avg score {testing_score}/100).")
    if average_type_safety is not None and average_type_safety < 50:
        flags.append(f"Below-average type safety across analyzed contributions ({average_type_safety}% typed).")
    if analyzed_repo_count == 1:
        flags.append("Score is based on a single repository - limited evidence.")
    return flags


def build_contributor_engineering_profile(
    login: str,
    avatar_url: str | None,
    total_commits: int,
    analyzed_repo_names: list[str],
    repo_reports: dict[str, dict],
) -> dict:
    """
    Aggregates one contributor's engineering profile from the already-computed
    per-repo reports (repo_analysis.analyze_repo() output) of the repos they
    meaningfully contributed to. Never calls OpenAI itself - purely arithmetic
    over evidence that already exists.
    """
    reports = [repo_reports[name]["report"] for name in analyzed_repo_names if name in repo_reports]
    type_safety_signals_list = [
        repo_reports[name]["type_safety_signals"] for name in analyzed_repo_names if name in repo_reports
    ]

    if not reports:
        return {
            "login": login,
            "avatar_url": avatar_url,
            "commit_count": total_commits,
            "repositories_contributed": 0,
            "documentation_score": None,
            "testing_score": None,
            "devops_score": None,
            "security_score": None,
            "project_maturity_score": None,
            "average_quality_score": None,
            "average_type_safety": None,
            "overall_engineering_score": None,
            "strengths": [],
            "weaknesses": [],
            "risk_flags": ["Not enough analyzed repository evidence to score this contributor in this run."],
            "summary": (
                f"{login} has {total_commits} commits in this organization, but none of their "
                "repositories were included in this run's analysis depth."
            ),
            "repositories": [],
        }

    def avg_category(category_name: str) -> int | None:
        scores = [score for score in (_category_score(report, category_name) for report in reports) if score is not None]
        return round(sum(scores) / len(scores)) if scores else None

    category_averages = {
        "Documentation": avg_category("Documentation"),
        "Testing": avg_category("Testing"),
        "DevOps": avg_category("DevOps"),
        "Security": avg_category("Security"),
        "Project Maturity": avg_category("Project Maturity"),
        "Code Quality": avg_category("Code Quality & Type Safety (AI Slop)"),
    }

    type_safety_ratios = [
        ratio for ratio in (_type_safety_ratio(signals) for signals in type_safety_signals_list) if ratio is not None
    ]
    average_type_safety = round(sum(type_safety_ratios) / len(type_safety_ratios)) if type_safety_ratios else None

    overall_engineering_score = round(sum(report["overall_score"] for report in reports) / len(reports))

    strengths = _dedupe_capped([item for report in reports for item in report.get("strengths", [])], cap=5)
    weaknesses = _dedupe_capped([item for report in reports for item in report.get("weaknesses", [])], cap=5)

    risk_flags = _build_risk_flags(category_averages["Testing"], average_type_safety, len(analyzed_repo_names))

    scored_categories = [(name, score) for name, score in category_averages.items() if score is not None]
    summary = (
        f"{login} contributed to {len(analyzed_repo_names)} of the organization's analyzed repositories "
        f"with an average engineering score of {overall_engineering_score}/100."
    )
    if len(scored_categories) >= 2:
        best_name, best_score = max(scored_categories, key=lambda item: item[1])
        worst_name, worst_score = min(scored_categories, key=lambda item: item[1])
        if best_name != worst_name:
            summary += f" Strongest category: {best_name} ({best_score}). Weakest: {worst_name} ({worst_score})."

    return {
        "login": login,
        "avatar_url": avatar_url,
        "commit_count": total_commits,
        "repositories_contributed": len(analyzed_repo_names),
        "documentation_score": category_averages["Documentation"],
        "testing_score": category_averages["Testing"],
        "devops_score": category_averages["DevOps"],
        "security_score": category_averages["Security"],
        "project_maturity_score": category_averages["Project Maturity"],
        "average_quality_score": category_averages["Code Quality"],
        "average_type_safety": average_type_safety,
        "overall_engineering_score": overall_engineering_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risk_flags": risk_flags,
        "summary": summary,
        "repositories": analyzed_repo_names,
    }
