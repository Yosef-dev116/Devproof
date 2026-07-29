from backend.app.scoring import calculate_credibility_score


def test_scales_with_stars_forks_and_commits():
    low = calculate_credibility_score(stars=10, forks=2, recent_commit_count=1)
    high = calculate_credibility_score(stars=1000, forks=200, recent_commit_count=10)
    assert high > low


def test_caps_at_100_for_very_popular_repos():
    score = calculate_credibility_score(stars=100_000, forks=10_000, recent_commit_count=30)
    assert score == 100


def test_zero_activity_scores_zero():
    assert calculate_credibility_score(stars=0, forks=0, recent_commit_count=0) == 0
