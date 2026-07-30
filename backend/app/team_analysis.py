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
