from backend.app.analysis import detect_signals


def test_detects_all_signals_when_present():
    paths = [
        "tests/test_main.py",
        ".github/workflows/ci.yml",
        "Dockerfile",
        ".env.example",
        "LICENSE",
        "src/main.py",
    ]
    signals = detect_signals(paths)
    assert signals["has_tests"] is True
    assert signals["has_ci"] is True
    assert signals["has_dockerfile"] is True
    assert signals["has_env_example"] is True
    assert signals["has_license"] is True
    assert signals["file_count"] == len(paths)


def test_detects_no_signals_for_bare_repo():
    paths = ["main.py", "README.md"]
    signals = detect_signals(paths)
    assert signals["has_tests"] is False
    assert signals["has_ci"] is False
    assert signals["has_dockerfile"] is False
    assert signals["has_env_example"] is False
    assert signals["has_license"] is False


def test_top_level_entries_are_deduplicated_and_sorted():
    paths = ["src/a.py", "src/b.py", "docs/readme.md", "README.md"]
    signals = detect_signals(paths)
    assert signals["top_level_entries"] == ["README.md", "docs", "src"]
