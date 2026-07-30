from backend.app.team_analysis import aggregate_contributors


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
