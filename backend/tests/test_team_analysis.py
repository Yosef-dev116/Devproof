from backend.app.team_analysis import (
    aggregate_contributors,
    select_top_contributors,
    find_meaningful_contributions,
    select_repos_to_analyze,
    build_contributor_engineering_profile,
)


def test_sums_commits_for_the_same_contributor_across_repos():
    contributors_by_repo = {
        "repo-a": [{"login": "alice", "avatar_url": "a.png", "contributions": 10}],
        "repo-b": [{"login": "alice", "avatar_url": "a.png", "contributions": 5}],
    }
    result = aggregate_contributors(contributors_by_repo)
    assert len(result) == 1
    assert result[0]["login"] == "alice"
    assert result[0]["total_commits"] == 15
    assert result[0]["repositories"] == ["repo-a", "repo-b"]


def test_keeps_different_contributors_separate():
    contributors_by_repo = {
        "repo-a": [
            {"login": "alice", "avatar_url": None, "contributions": 10},
            {"login": "bob", "avatar_url": None, "contributions": 3},
        ],
    }
    result = aggregate_contributors(contributors_by_repo)
    logins = {entry["login"] for entry in result}
    assert logins == {"alice", "bob"}


def test_sorted_by_total_commits_descending():
    contributors_by_repo = {
        "repo-a": [
            {"login": "low", "avatar_url": None, "contributions": 2},
            {"login": "high", "avatar_url": None, "contributions": 50},
        ],
    }
    result = aggregate_contributors(contributors_by_repo)
    assert [entry["login"] for entry in result] == ["high", "low"]


def test_empty_input_returns_empty_list():
    assert aggregate_contributors({}) == []


def _contributor(login: str, total_commits: int) -> dict:
    return {"login": login, "avatar_url": None, "total_commits": total_commits, "repositories": []}


def test_select_top_contributors_limits_and_sorts():
    contributors = [_contributor("low", 5), _contributor("high", 100), _contributor("mid", 40)]
    result = select_top_contributors(contributors, limit=2)
    assert [c["login"] for c in result] == ["high", "mid"]


def test_find_meaningful_contributions_applies_commit_floor():
    contributors_by_repo = {
        "repo-a": [{"login": "alice", "contributions": 10}],
        "repo-b": [{"login": "alice", "contributions": 2}],
        "repo-c": [{"login": "bob", "contributions": 20}],
    }
    result = find_meaningful_contributions("alice", contributors_by_repo, min_commits=5)
    assert result == ["repo-a"]


def test_select_repos_to_analyze_dedupes_and_caps():
    contributor_repo_map = {
        "alice": ["shared-repo", "alice-only"],
        "bob": ["shared-repo", "bob-only"],
    }
    result = select_repos_to_analyze(contributor_repo_map, max_repos=2)
    assert "shared-repo" in result  # referenced by 2 contributors, ranks first
    assert len(result) == 2


def _fake_report(overall_score: int, category_scores: dict, strengths: list[str], weaknesses: list[str]) -> dict:
    return {
        "overall_score": overall_score,
        "categories": [{"name": name, "score": score, "comment": "", "details": ""} for name, score in category_scores.items()],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": [],
        "learning_roadmap": [],
    }


def _fake_type_safety_signals(typed_functions: int, total_functions: int) -> dict:
    return {
        "files_sampled": 1,
        "python_functions_found": total_functions,
        "python_functions_with_type_hints": typed_functions,
        "js_ts_files_found": 0,
        "typed_ts_files_found": 0,
        "typescript_any_usages": 0,
        "typescript_interface_or_type_declarations": 0,
    }


def test_build_contributor_engineering_profile_averages_across_repos():
    repo_reports = {
        "repo-a": {
            "report": _fake_report(
                80,
                {"Documentation": 90, "Testing": 70, "DevOps": 80, "Security": 80, "Project Maturity": 80,
                 "Code Quality & Type Safety (AI Slop)": 90},
                strengths=["Good docs"],
                weaknesses=["Few tests"],
            ),
            "type_safety_signals": _fake_type_safety_signals(8, 10),
        },
        "repo-b": {
            "report": _fake_report(
                60,
                {"Documentation": 50, "Testing": 50, "DevOps": 60, "Security": 60, "Project Maturity": 60,
                 "Code Quality & Type Safety (AI Slop)": 50},
                strengths=["Good docs"],
                weaknesses=["No CI"],
            ),
            "type_safety_signals": _fake_type_safety_signals(2, 10),
        },
    }

    profile = build_contributor_engineering_profile(
        login="alice",
        avatar_url="a.png",
        total_commits=42,
        analyzed_repo_names=["repo-a", "repo-b"],
        repo_reports=repo_reports,
    )

    assert profile["repositories_contributed"] == 2
    assert profile["overall_engineering_score"] == 70  # avg(80, 60)
    assert profile["documentation_score"] == 70  # avg(90, 50)
    assert profile["average_type_safety"] == 50  # avg(80%, 20%)
    assert profile["strengths"] == ["Good docs"]  # deduped
    assert set(profile["weaknesses"]) == {"Few tests", "No CI"}


def test_build_contributor_engineering_profile_flags_insufficient_evidence():
    profile = build_contributor_engineering_profile(
        login="ghost",
        avatar_url=None,
        total_commits=12,
        analyzed_repo_names=["repo-that-was-not-analyzed"],
        repo_reports={},
    )
    assert profile["repositories_contributed"] == 0
    assert profile["overall_engineering_score"] is None
    assert profile["risk_flags"] == ["Not enough analyzed repository evidence to score this contributor in this run."]


def test_build_contributor_engineering_profile_flags_low_testing_and_type_safety():
    repo_reports = {
        "repo-a": {
            "report": _fake_report(
                40,
                {"Documentation": 40, "Testing": 20, "DevOps": 40, "Security": 40, "Project Maturity": 40,
                 "Code Quality & Type Safety (AI Slop)": 30},
                strengths=[],
                weaknesses=[],
            ),
            "type_safety_signals": _fake_type_safety_signals(1, 10),
        },
    }
    profile = build_contributor_engineering_profile(
        login="bob", avatar_url=None, total_commits=5,
        analyzed_repo_names=["repo-a"], repo_reports=repo_reports,
    )
    assert any("testing" in flag.lower() for flag in profile["risk_flags"])
    assert any("type safety" in flag.lower() for flag in profile["risk_flags"])
    assert any("single repository" in flag.lower() for flag in profile["risk_flags"])
