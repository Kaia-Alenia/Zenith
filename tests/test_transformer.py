def test_analyze_file_missing():
    from zenith.transformer.ast_rewriter import analyze_file
    assert analyze_file("/path/that/does/not/exist.py") == []

def test_analyze_stdlib_only(tmp_path):
    from zenith.transformer.ast_rewriter import analyze_stdlib_only, analyze_file
    p = tmp_path / "test.py"
    p.write_text("import os\nimport numpy as np\n")
    parsed = analyze_file(str(p))
    res = analyze_stdlib_only(str(p), parsed_modules=parsed)
    assert "os" in res
    assert "numpy" not in res

def test_analyze_third_party(tmp_path):
    from zenith.transformer.ast_rewriter import analyze_third_party, analyze_file
    p = tmp_path / "test.py"
    p.write_text("import os\nimport numpy as np\n")
    parsed = analyze_file(str(p))
    res = analyze_third_party(str(p), parsed_modules=parsed)
    assert "numpy" in res
    assert "os" not in res

def test_analyze_stdlib_only_with_cached_parsed():
    from zenith.transformer.ast_rewriter import analyze_stdlib_only
    res = analyze_stdlib_only("dummy.py", parsed_modules=["os", "numpy", "json"])
    assert "os" in res
    assert "json" in res
    assert "numpy" not in res

def test_analyze_third_party_with_cached_parsed():
    from zenith.transformer.ast_rewriter import analyze_third_party
    res = analyze_third_party("dummy.py", parsed_modules=["os", "numpy", "requests"])
    assert "numpy" in res
    assert "requests" in res
    assert "os" not in res

def run_all():
    print("Testing zenith.transformer.ast_rewriter")
    import tempfile
    from pathlib import Path

    test_analyze_file_missing()
    print("  [PASS] test_analyze_file_missing")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_analyze_stdlib_only(tmp)
        print("  [PASS] test_analyze_stdlib_only")
        test_analyze_third_party(tmp)
        print("  [PASS] test_analyze_third_party")

    test_analyze_stdlib_only_with_cached_parsed()
    print("  [PASS] test_analyze_stdlib_only_with_cached_parsed")

    test_analyze_third_party_with_cached_parsed()
    print("  [PASS] test_analyze_third_party_with_cached_parsed")

    print("All tests passed!")

if __name__ == "__main__":
    run_all()
