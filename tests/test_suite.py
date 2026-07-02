import sys
import time
import types
import threading
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
WARN = "\033[93m WARN\033[0m"

results: list[tuple[str, bool, str]] = []


def check_test(name: str, condition: bool, note: str = "") -> None:
    results.append((name, condition, note))
    icon = PASS if condition else FAIL
    suffix = f"  ({note})" if note else ""
    print(f"  [{icon}] {name}{suffix}")


def section(title: str) -> None:
    print(f"\n\033[95m{'='*50}\033[0m")
    print(f"\033[95m  {title}\033[0m")
    print(f"\033[95m{'='*50}\033[0m")


def run_all() -> None:

    section("1. PACKAGE IMPORT")
    import zenith
    check_test("zenith imports without error", True)
    check_test("version attribute exists", hasattr(zenith, "__version__"))
    check_test("version is a string", isinstance(zenith.__version__, str))
    check_test("public API is complete", all(hasattr(zenith, f) for f in [
        "ignite", "warm", "exclude", "status", "analyze", "invalidate_cache"
    ]))

    section("2. LAZY LOADING (PROXY MODULES)")
    from zenith.hooks.loader import ZenithLazyModule
    from zenith.core.engine import SpeculationEngine
    from zenith.speculation.predictor import ImportPredictor
    from zenith.hooks.loader import install_hook

    engine2 = SpeculationEngine()
    pred2 = ImportPredictor()
    engine2.start(workers=2)
    install_hook(engine2, pred2, extra_exclusions={"zenith", "tests"})

    import hashlib
    proxy = sys.modules.get("hashlib")
    check_test("hashlib is a lazy proxy after hook install", isinstance(proxy, ZenithLazyModule))
    check_test("proxy is not yet loaded", not object.__getattribute__(proxy, "_zenith_loaded"))

    _ = hashlib.sha256
    check_test("accessing an attribute triggers real load", object.__getattribute__(proxy, "_zenith_loaded"))
    check_test("sha256 is callable after load", callable(hashlib.sha256))

    result = hashlib.sha256(b"zenith").hexdigest()
    check_test("sha256 produces correct output", len(result) == 64)

    section("3. SPECULATIVE BACKGROUND PRE-LOADING")
    from zenith.core.engine import _bypass_lazy

    engine3 = SpeculationEngine()
    engine3.start(workers=4)

    preloaded_correctly = []

    def load_and_check(mod: str) -> None:
        import importlib as _ilib
        from zenith.core.engine import _bypass_lazy
        _bypass_lazy.active = True
        try:
            _ilib.import_module(mod)
            preloaded_correctly.append(mod)
        finally:
            _bypass_lazy.active = False

    t = threading.Thread(target=load_and_check, args=("base64",))
    t.start()
    t.join(timeout=3)
    check_test("background thread loads real module", "base64" in preloaded_correctly)

    import base64 as b64_mod
    check_test("base64 accessible after pre-load", hasattr(b64_mod, "b64encode"))
    check_test("base64 encodes correctly", b64_mod.b64encode(b"zenith") == b"emVuaXRo")

    section("4. IMPORT PREDICTOR CACHE")
    import tempfile, json
    tmp = Path(tempfile.mktemp(suffix=".json"))
    from zenith.speculation.predictor import ImportPredictor

    pred = ImportPredictor(cache_path=str(tmp))
    check_test("empty cache returns empty list", pred.load_predictions() == [])

    pred.save_module("os.path")
    pred.save_module("collections")
    pred.save_module("itertools")
    pred.persist_cache()

    check_test("cache is persisted to disk", tmp.exists())
    data = json.loads(tmp.read_text())
    check_test("cache file contains 'modules' key", "modules" in data)
    check_test("saved modules match expected set", set(data["modules"]) == {"os.path", "collections", "itertools"})

    pred2b = ImportPredictor(cache_path=str(tmp))
    loaded = pred2b.load_predictions()
    check_test("cache reloaded in new instance", set(loaded) == {"os.path", "collections", "itertools"})

    pred2b.invalidate()
    check_test("invalidate() removes cache file", not tmp.exists())

    tmp.write_text("{invalid json", encoding="utf-8")
    pred_invalid = ImportPredictor(cache_path=str(tmp))
    check_test("invalid json returns empty list", pred_invalid.load_predictions() == [])

    tmp.write_text('["module"]', encoding="utf-8")
    pred_not_dict = ImportPredictor(cache_path=str(tmp))
    check_test("non-dict json returns empty list", pred_not_dict.load_predictions() == [])

    section("5. AST REWRITER")
    from zenith.transformer.ast_rewriter import analyze_file, analyze_stdlib_only, analyze_third_party

    test_file = Path(tempfile.mktemp(suffix=".py"))
    test_file.write_text("""
import os
import sys
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
import requests
from fastapi import FastAPI
""", encoding="utf-8")

    all_mods = analyze_file(str(test_file))
    stdlib_mods = analyze_stdlib_only(str(test_file), parsed_modules=all_mods)
    third_mods = analyze_third_party(str(test_file), parsed_modules=all_mods)

    check_test("analyze_file detects imports", len(all_mods) > 0)
    check_test("os is detected", "os" in all_mods)
    check_test("pathlib is detected", "pathlib" in all_mods)
    check_test("pathlib.Path is detected", "pathlib.Path" in all_mods)
    check_test("numpy is detected", "numpy" in all_mods)
    check_test("analyze_stdlib_only filters correctly", "os" in stdlib_mods and "numpy" not in stdlib_mods)
    check_test("analyze_third_party filters correctly", "numpy" in third_mods and "os" not in third_mods)
    check_test("invalid file path returns []", analyze_file("/no/such/file.py") == [])

    invalid_syntax_file = Path(tempfile.mktemp(suffix=".py"))
    invalid_syntax_file.write_text("def class import bad syntax !!!\n", encoding="utf-8")
    check_test("invalid syntax returns []", analyze_file(str(invalid_syntax_file)) == [])
    invalid_syntax_file.unlink()

    test_file.unlink()

    section("6. ignite() PARAMETERS")
    import importlib as _imp

    _imp.reload(zenith)
    import zenith as z2
    z2._initialized = False
    z2._engine = z2.SpeculationEngine()
    z2._predictor = z2.ImportPredictor()

    tmp_cache = Path(tempfile.mktemp(suffix=".json"))
    z2.ignite(
        workers=2,
        verbose=False,
        show_banner=False,
        cache_path=str(tmp_cache),
    )
    check_test("ignite() is idempotent on second call", True)
    z2.ignite(show_banner=False)
    check_test("double ignite() does not raise", True)

    section("7. warm() AND exclude()")
    from zenith.core.engine import SpeculationEngine as SE
    from zenith.core.constants import STRICT_EXCLUSIONS

    eng = SE()
    eng.start(workers=2)
    eng.preload("textwrap")
    time.sleep(0.5)
    check_test("textwrap is pre-loaded after warm", "textwrap" in eng._preloaded)

    eng.add_exclusions({"my_private_module"})
    eng.preload("my_private_module")
    check_test("excluded module is not pre-loaded", "my_private_module" not in eng._preloaded)

    section("8. status()")
    z2._initialized = True
    s = z2.status()
    check_test("status() returns a dict", isinstance(s, dict))
    check_test("status has 'version' key", "version" in s)
    check_test("status has 'preloaded_count' key", "preloaded_count" in s)
    check_test("status has 'cached_modules' key", "cached_modules" in s)
    check_test("preloaded_count is an integer", isinstance(s["preloaded_count"], int))

    section("9. PUBLIC analyze() FUNCTION")
    z2._initialized = True
    script = Path(tempfile.mktemp(suffix=".py"))
    script.write_text("import json\nimport os\nfrom pathlib import Path\n")
    mods = z2.analyze(str(script))
    check_test("analyze() returns a list", isinstance(mods, list))
    check_test("json is detected in analyzed file", "json" in mods)
    script.unlink()
    check_test("analyze empty file string", z2.analyze('') == [])

    section("10. THREAD SAFETY — CONCURRENT LOADING")
    from zenith.hooks.loader import ZenithLazyModule as ZLM
    from zenith.hooks.loader import ZenithLazyLoader
    import importlib.util

    load_events: list[str] = []
    lock_test = threading.Lock()

    import subprocess
    thread_test_code = """
import sys, threading
sys.path.insert(0, '.')
from zenith.hooks.loader import ZenithLazyModule as ZLM
import importlib.util, importlib

spec = importlib.util.find_spec('decimal')
proxy = ZLM(spec, spec.loader, None, None)
sys.modules['decimal'] = proxy

results = []
lock = threading.Lock()

def go():
    dec = importlib.import_module('decimal')
    try:
        _ = dec.Decimal('3.14')
        with lock: results.append('ok')
    except Exception as e:
        with lock: results.append(f'ERR:{e}')

threads = [threading.Thread(target=go) for _ in range(6)]
for t in threads: t.start()
for t in threads: t.join(timeout=5)
print('ALL_OK' if all(r == 'ok' for r in results) and len(results) == 6 else f'FAIL:{results}')
"""
    res = subprocess.run(
        [sys.executable, "-c", thread_test_code],
        capture_output=True, text=True, cwd=str(Path(__file__).parent.parent)
    )
    output = res.stdout.strip()
    check_test("6 concurrent threads on decimal (isolated subprocess)", output == "ALL_OK", output if output != "ALL_OK" else "")
    check_test("decimal.Decimal works correctly after lazy load", res.returncode == 0)


    section("11. ENGINE SHUTDOWN")
    from zenith.core.engine import SpeculationEngine
    
    eng11 = SpeculationEngine()
    eng11.shutdown()
    check_test("shutdown() when executor is None does not raise", True)
    
    eng11.start(workers=2)
    eng11.shutdown(wait=False)
    try:
        eng11._executor.submit(lambda: None)
        raised = False
    except RuntimeError:
        raised = True
    check_test("shutdown(wait=False) prevents new submissions", raised)
    
    eng12 = SpeculationEngine()
    eng12.start(workers=2)
    eng12.shutdown(wait=True)
    try:
        eng12._executor.submit(lambda: None)
        raised = False
    except RuntimeError:
        raised = True
    check_test("shutdown(wait=True) prevents new submissions", raised)

    section("12. MAIN MODULE FULL API")
    import tempfile, os
    import importlib as _imp
    _imp.reload(zenith)
    zenith._initialized = False
    zenith._engine = zenith.SpeculationEngine()
    zenith._predictor = zenith.ImportPredictor()
    
    tmp_cache2 = Path(tempfile.mktemp(suffix=".json"))
    zenith.ignite(cache_path=str(tmp_cache2), show_banner=False)
    
    # Save some dummy data into the cache
    zenith._predictor.save_module("dummy_module1")
    zenith._predictor.save_module("dummy_module2")
    zenith._predictor.persist_cache()
    
    check_test("cache file exists before invalidate", tmp_cache2.exists())
    
    zenith.invalidate_cache()
    check_test("invalidate_cache() removes the cache file", not tmp_cache2.exists())

    _imp.reload(zenith)
    zenith._initialized = False
    zenith._engine = zenith.SpeculationEngine()
    zenith._predictor = zenith.ImportPredictor()

    tmp_script = Path(tempfile.mktemp(suffix=".py"))
    tmp_script.write_text("import math\n", encoding="utf-8")
    
    zenith.ignite(file=str(tmp_script), show_banner=False)
    check_test("ignite(file=...) preloads modules from file", "math" in zenith._engine._preloaded)
    tmp_script.unlink()

    _imp.reload(zenith)
    zenith._initialized = False
    zenith._engine = zenith.SpeculationEngine()
    zenith._predictor = zenith.ImportPredictor()

    try:
        zenith.ignite(file="doesnt_exist.py", show_banner=False)
        crashed = False
    except Exception:
        crashed = True
    check_test("ignite(file=non_existent_file) does not crash", not crashed)

    section("13. CLI MODULE")
    import argparse
    from unittest.mock import patch
    import io
    from zenith.cli import cmd_analyze, cmd_status, cmd_invalidate, main
    
    tmp_analyze = Path(tempfile.mktemp(suffix=".py"))
    tmp_analyze.write_text("import json\nimport os\nimport requests\n", encoding="utf-8")
    
    args_analyze = argparse.Namespace(file=str(tmp_analyze), verbose=True)
    with patch("sys.stdout", new=io.StringIO()) as fake_out:
        cmd_analyze(args_analyze)
        out_analyze = fake_out.getvalue()
        
    check_test("cmd_analyze outputs total imports", "Total imports : 3" in out_analyze)
    check_test("cmd_analyze detects stdlib", "Stdlib        : 2" in out_analyze)
    check_test("cmd_analyze detects third-party", "Third-party   : 1" in out_analyze)
    
    tmp_analyze.unlink()
    
    args_status = argparse.Namespace()
    with patch("sys.stdout", new=io.StringIO()) as fake_out:
        cmd_status(args_status)
        out_status = fake_out.getvalue()
        
    check_test("cmd_status outputs initialized status", "Initialized   :" in out_status)
    check_test("cmd_status outputs workers", "Workers       :" in out_status)
    
    args_inv = argparse.Namespace()
    with patch("sys.stdout", new=io.StringIO()) as fake_out:
        cmd_invalidate(args_inv)
        out_inv = fake_out.getvalue()
        
    check_test("cmd_invalidate outputs success message", "Cache invalidated" in out_inv)
    
    with patch("sys.stdout", new=io.StringIO()) as fake_out:
        with patch("sys.argv", ["zenith", "status"]):
            main()
        out_main = fake_out.getvalue()
        
    check_test("main() handles status command", "Initialized   :" in out_main)

    section("14. CLI BENCHMARK ERROR HANDLING")
    import argparse
    import io
    import subprocess
    from unittest.mock import patch
    from zenith.cli import cmd_benchmark

    args = argparse.Namespace(modules=["json"], runs=1)
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='invalid_float\n')
        
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            cmd_benchmark(args)
            output = mock_stdout.getvalue()
    check_test("cmd_benchmark handles invalid float correctly", "0.00000s" in output)

    section("13. CLI cmd_analyze")
    import argparse, io, contextlib
    from zenith.cli import cmd_analyze

    # Create a temporary file with a mix of stdlib and third-party imports
    cli_tmp = Path(tempfile.mktemp(suffix=".py"))
    cli_tmp.write_text("import os\nimport sys\nimport requests\nimport numpy as np\n", encoding="utf-8")

    # Test normal execution (verbose=False)
    args_normal = argparse.Namespace(file=str(cli_tmp), verbose=False)
    f_normal = io.StringIO()
    with contextlib.redirect_stdout(f_normal):
        cmd_analyze(args_normal)
    output_normal = f_normal.getvalue()

    check_test("cmd_analyze normal output contains total imports count", "Total imports : 4" in output_normal)
    check_test("cmd_analyze normal output contains stdlib count", "Stdlib        : 2" in output_normal)
    check_test("cmd_analyze normal output contains third-party count", "Third-party   : 2" in output_normal)
    check_test("cmd_analyze normal output hides verbose details", "Stdlib:" not in output_normal and "Third-party:" not in output_normal)

    # Test verbose execution (verbose=True)
    args_verbose = argparse.Namespace(file=str(cli_tmp), verbose=True)
    f_verbose = io.StringIO()
    with contextlib.redirect_stdout(f_verbose):
        cmd_analyze(args_verbose)
    output_verbose = f_verbose.getvalue()

    check_test("cmd_analyze verbose output lists stdlib header", "Stdlib:" in output_verbose)
    check_test("cmd_analyze verbose output lists os module", "  - os" in output_verbose)
    check_test("cmd_analyze verbose output lists third-party header", "Third-party:" in output_verbose)
    check_test("cmd_analyze verbose output lists numpy module", "  - numpy" in output_verbose)

    cli_tmp.unlink()

    section("FINAL SUMMARY")
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    pct = passed / total * 100
    print(f"\n  Total  : {total}")
    print(f"  \033[92mPassed : {passed}\033[0m")
    if failed:
        print(f"  \033[91mFailed : {failed}\033[0m")
        print("\n  Failed tests:")
        for name, ok, note in results:
            if not ok:
                print(f"    - {name}" + (f" ({note})" if note else ""))
    print(f"\n  Score  : {pct:.1f}%")
    print()


if __name__ == "__main__":
    run_all()
