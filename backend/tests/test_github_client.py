from backend.app.github_client import parse_github_url


def test_parses_owner_and_repo_from_url():
    assert parse_github_url("https://github.com/octocat/Hello-World") == ("octocat", "Hello-World")


def test_parses_url_with_trailing_slash():
    assert parse_github_url("https://github.com/octocat/Hello-World/") == ("octocat", "Hello-World")
