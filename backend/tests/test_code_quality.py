from backend.app.code_quality import detect_type_safety_signals, select_sample_files


def test_select_sample_files_excludes_trivial_and_vendor_paths():
    entries = [
        {"path": "backend/app/main.py", "size": 5000},
        {"path": "backend/app/__init__.py", "size": 0},
        {"path": "node_modules/react/index.js", "size": 2000},
        {"path": "frontend/src/App.tsx", "size": 8000},
    ]
    selected = select_sample_files(entries, max_files=10)
    assert "backend/app/main.py" in selected
    assert "frontend/src/App.tsx" in selected
    assert "backend/app/__init__.py" not in selected
    assert "node_modules/react/index.js" not in selected


def test_select_sample_files_prefers_larger_files():
    entries = [
        {"path": "a.py", "size": 100},
        {"path": "b.py", "size": 9000},
        {"path": "c.py", "size": 500},
    ]
    selected = select_sample_files(entries, max_files=1)
    assert selected == ["b.py"]


def test_select_sample_files_caps_per_top_level_directory():
    entries = [{"path": f"src/file{i}.py", "size": 1000 - i} for i in range(5)]
    selected = select_sample_files(entries, max_files=10, max_per_top_dir=2)
    assert len(selected) == 2


def test_detects_fully_typed_python_functions():
    content = "def add(x: int, y: int) -> int:\n    return x + y\n"
    signals = detect_type_safety_signals({"a.py": content})
    assert signals["python_functions_found"] == 1
    assert signals["python_functions_with_type_hints"] == 1


def test_detects_untyped_python_functions():
    content = "def add(x, y):\n    return x + y\n"
    signals = detect_type_safety_signals({"a.py": content})
    assert signals["python_functions_found"] == 1
    assert signals["python_functions_with_type_hints"] == 0


def test_detects_typescript_interfaces_and_any_usage():
    content = "interface Foo { bar: string }\nfunction f(x: any): any { return x }\n"
    signals = detect_type_safety_signals({"a.ts": content})
    assert signals["typescript_interface_or_type_declarations"] == 1
    assert signals["typescript_any_usages"] == 2


def test_plain_js_file_counts_as_untyped():
    signals = detect_type_safety_signals({"a.js": "function f(x) { return x }"})
    assert signals["js_ts_files_found"] == 1
    assert signals["typed_ts_files_found"] == 0
