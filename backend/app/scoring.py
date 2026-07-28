def calculate_credibility_score(stars: int, forks: int, recent_commit_count: int) -> int:
    raw_score = stars * 0.01 + forks * 0.02 + recent_commit_count * 2
    return min(100, round(raw_score))
