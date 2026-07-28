def detect_signals(file_paths: list[str]) -> dict:
    lowered = [path.lower() for path in file_paths]

    has_tests = any("test" in path for path in lowered)
    has_ci = any(path.startswith(".github/workflows/") for path in lowered)
    has_dockerfile = any(path == "dockerfile" or path.endswith("/dockerfile") for path in lowered)
    has_env_example = any(".env.example" in path or ".env.sample" in path for path in lowered)
    has_license = any(path in ("license", "license.md", "license.txt") for path in lowered)
    top_level_entries = sorted({path.split("/")[0] for path in file_paths})

    return {
        "has_tests": has_tests,
        "has_ci": has_ci,
        "has_dockerfile": has_dockerfile,
        "has_env_example": has_env_example,
        "has_license": has_license,
        "top_level_entries": top_level_entries,
        "file_count": len(file_paths),
    }
