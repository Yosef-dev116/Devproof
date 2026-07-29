import re

SOURCE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx")
EXCLUDED_PATH_FRAGMENTS = ("node_modules/", "dist/", "build/", "__pycache__/", ".venv/", "venv/")
TRIVIAL_FILENAMES = {"__init__.py", "__main__.py", "setup.py"}

PYTHON_DEF_PATTERN = re.compile(r"def\s+\w+\s*\(([^)]*)\)\s*(->\s*[^:]+)?:")
TS_ANY_PATTERN = re.compile(r":\s*any\b")
TS_INTERFACE_OR_TYPE_PATTERN = re.compile(r"^\s*(export\s+)?(interface|type)\s+\w+", re.MULTILINE)


def select_sample_files(file_entries: list[dict], max_files: int = 6, max_per_top_dir: int = 3) -> list[str]:
    candidates = [
        entry
        for entry in file_entries
        if entry["path"].endswith(SOURCE_EXTENSIONS)
        and not any(fragment in entry["path"] for fragment in EXCLUDED_PATH_FRAGMENTS)
        and entry["path"].rsplit("/", 1)[-1] not in TRIVIAL_FILENAMES
    ]

    # Prefer larger files first - more likely to contain substantial real
    # logic rather than trivial re-exports or near-empty stub files.
    candidates.sort(key=lambda entry: entry["size"], reverse=True)

    selected: list[str] = []
    per_top_dir_count: dict[str, int] = {}
    for entry in candidates:
        top_dir = entry["path"].split("/")[0]
        if per_top_dir_count.get(top_dir, 0) >= max_per_top_dir:
            continue
        selected.append(entry["path"])
        per_top_dir_count[top_dir] = per_top_dir_count.get(top_dir, 0) + 1
        if len(selected) >= max_files:
            break
    return selected


def detect_type_safety_signals(file_contents: dict[str, str]) -> dict:
    python_functions_found = 0
    python_functions_with_type_hints = 0
    js_ts_files_found = 0
    typed_ts_files_found = 0
    any_count = 0
    interface_count = 0

    for path, content in file_contents.items():
        if path.endswith(".py"):
            for match in PYTHON_DEF_PATTERN.finditer(content):
                python_functions_found += 1
                params, return_annotation = match.group(1), match.group(2)
                if ":" in params or return_annotation:
                    python_functions_with_type_hints += 1
        elif path.endswith((".ts", ".tsx", ".js", ".jsx")):
            js_ts_files_found += 1
            if path.endswith((".ts", ".tsx")):
                typed_ts_files_found += 1
            any_count += len(TS_ANY_PATTERN.findall(content))
            interface_count += len(TS_INTERFACE_OR_TYPE_PATTERN.findall(content))

    return {
        "files_sampled": len(file_contents),
        "python_functions_found": python_functions_found,
        "python_functions_with_type_hints": python_functions_with_type_hints,
        "js_ts_files_found": js_ts_files_found,
        "typed_ts_files_found": typed_ts_files_found,
        "typescript_any_usages": any_count,
        "typescript_interface_or_type_declarations": interface_count,
    }
