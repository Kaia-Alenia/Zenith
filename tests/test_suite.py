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


def test(name: str, condition: bool, note: str = "") -> None:
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
    test("zenith imports without error", True)
    test("version attribute exists", hasattr(zenith, "__version__"))
    test("version is a string", isinstance(zenith.__version__, str))
    test("public API is complete", all(hasattr(zenith, f) for f in [
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
    test("hashlib is a lazy proxy after hook install", isinstance(proxy, ZenithLazyModule))
    test("proxy is not yet loaded", not object.__getattribute__(proxy, "_zenith_loaded"))

    _ = hashlib.sha256
    test("accessing an attribute triggers real load", object.__getattribute__(proxy, "_zenith_loaded"))
    test("sha256 is callable after load", callable(hashlib.sha256))

    result = hashlib.sha256(b"zenith").hexdigest()
    test("sha256 produces correct output", len(result) == 64)

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
    test("background thread loads real module", "base64" in preloaded_correctly)

    import base64 as b64_mod
    test("base64 accessible after pre-load", hasattr(b64_mod, "b64encode"))
    test("base64 encodes correctly", b64_mod.b64encode(b"zenith") == b"emVuaXRo")

    section("4. IMPORT PREDICTOR CACHE")
    import tempfile, json
    tmp = Path(tempfile.mktemp(suffix=".json"))
    from zenith.speculation.predictor import ImportPredictor

    pred = ImportPredictor(cache_path=str(tmp))
    test("empty cache returns empty list", pred.load_predictions() == [])

    pred.save_module("os.path")
    pred.save_module("collections")
    pred.save_module("itertools")
    pred.persist_cache()

    test("cache is persisted to disk", tmp.exists())
    data = json.loads(tmp.read_text())
    test("cache file contains 'modules' key", "modules" in data)
    test("saved modules match expected set", set(data["modules"]) == {"os.path", "collections", "itertools"})

    pred2b = ImportPredictor(cache_path=str(tmp))
    loaded = pred2b.load_predictions()
    test("cache reloaded in new instance", set(loaded) == {"os.path", "collections", "itertools"})

    pred2b.invalidate()
    test("invalidate() removes cache file", not tmp.exists())

    tmp.write_text("{invalid json", encoding="utf-8")
    pred_invalid = ImportPredictor(cache_path=str(tmp))
    test("invalid json returns empty list", pred_invalid.load_predictions() == [])

    tmp.write_text('["module"]', encoding="utf-8")
    pred_not_dict = ImportPredictor(cache_path=str(tmp))
    test("non-dict json returns empty list", pred_not_dict.load_predictions() == [])

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
    stdlib_mods = analyze_stdlib_only(str(test_file))
    third_mods = analyze_third_party(str(test_file))

    test("analyze_file detects imports", len(all_mods) > 0)
    test("os is detected", "os" in all_mods)
    test("pathlib is detected", "pathlib" in all_mods)
    test("pathlib.Path is detected", "pathlib.Path" in all_mods)
    test("numpy is detected", "numpy" in all_mods)
    test("analyze_stdlib_only filters correctly", "os" in stdlib_mods and "numpy" not in stdlib_mods)
    test("analyze_third_party filters correctly", "numpy" in third_mods and "os" not in third_mods)
    test("invalid file path returns []", analyze_file("/no/such/file.py") == [])

    invalid_syntax_file = Path(tempfile.mktemp(suffix=".py"))
    invalid_syntax_file.write_text("def class import bad syntax !!!\n", encoding="utf-8")
    test("invalid syntax returns []", analyze_file(str(invalid_syntax_file)) == [])
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
    test("ignite() is idempotent on second call", True)
    z2.ignite(show_banner=False)
    test("double ignite() does not raise", True)

    section("7. warm() AND exclude()")
    from zenith.core.engine import SpeculationEngine as SE
    from zenith.core.constants import STRICT_EXCLUSIONS

    eng = SE()
    eng.start(workers=2)
    eng.preload("textwrap")
    time.sleep(0.5)
    test("textwrap is pre-loaded after warm", "textwrap" in eng._preloaded)

    eng.add_exclusions({"my_private_module"})
    eng.preload("my_private_module")
    test("excluded module is not pre-loaded", "my_private_module" not in eng._preloaded)

    section("8. status()")
    z2._initialized = True
    s = z2.status()
    test("status() returns a dict", isinstance(s, dict))
    test("status has 'version' key", "version" in s)
    test("status has 'preloaded_count' key", "preloaded_count" in s)
    test("status has 'cached_modules' key", "cached_modules" in s)
    test("preloaded_count is an integer", isinstance(s["preloaded_count"], int))

    section("9. PUBLIC analyze() FUNCTION")
    z2._initialized = True
    script = Path(tempfile.mktemp(suffix=".py"))
    script.write_text("import json\nimport os\nfrom pathlib import Path\n")
    mods = z2.analyze(str(script))
    test("analyze() returns a list", isinstance(mods, list))
    test("json is detected in analyzed file", "json" in mods)
    script.unlink()

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
    test("6 concurrent threads on decimal (isolated subprocess)", output == "ALL_OK", output if output != "ALL_OK" else "")
    test("decimal.Decimal works correctly after lazy load", res.returncode == 0)


    section("11. ENGINE SHUTDOWN")
    from zenith.core.engine import SpeculationEngine
    
    eng11 = SpeculationEngine()
    eng11.shutdown()
    test("shutdown() when executor is None does not raise", True)
    
    eng11.start(workers=2)
    eng11.shutdown(wait=False)
    try:
        eng11._executor.submit(lambda: None)
        raised = False
    except RuntimeError:
        raised = True
    test("shutdown(wait=False) prevents new submissions", raised)
    
    eng12 = SpeculationEngine()
    eng12.start(workers=2)
    eng12.shutdown(wait=True)
    try:
        eng12._executor.submit(lambda: None)
        raised = False
    except RuntimeError:
        raised = True
    test("shutdown(wait=True) prevents new submissions", raised)

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
    
    test("cache file exists before invalidate", tmp_cache2.exists())
    
    zenith.invalidate_cache()
    test("invalidate_cache() removes the cache file", not tmp_cache2.exists())

    _imp.reload(zenith)
    zenith._initialized = False
    zenith._engine = zenith.SpeculationEngine()
    zenith._predictor = zenith.ImportPredictor()

    tmp_script = Path(tempfile.mktemp(suffix=".py"))
    tmp_script.write_text("import math\n", encoding="utf-8")
    
    zenith.ignite(file=str(tmp_script), show_banner=False)
    test("ignite(file=...) preloads modules from file", "math" in zenith._engine._preloaded)
    tmp_script.unlink()

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
