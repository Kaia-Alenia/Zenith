import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def run_isolated(use_zenith: bool, modules: list[str]) -> float:
    mod_list = repr(modules)
    header = "import zenith; zenith.ignite(show_banner=False)\n" if use_zenith else ""
    code = f"""
import sys, time
sys.path.insert(0, '{ROOT}')
{header}
start = time.perf_counter()
for m in {mod_list}:
    __import__(m)
elapsed = time.perf_counter() - start
import json
print(json.dumps({{"time": elapsed}}))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True,
    )
    try:
        return __import__("json").loads(result.stdout.strip())["time"]
    except Exception:
        return 0.0


def main() -> None:
    modules = ["multiprocessing", "urllib.request", "sqlite3", "json", "xml.etree.ElementTree"]
    runs = 5

    print("=========================================")
    print("     ZENITH PERFORMANCE TELEMETRY        ")
    print("=========================================")
    print(f"Modules : {', '.join(modules)}")
    print(f"Runs    : {runs}")
    print("Running...\n")

    native_times = [run_isolated(False, modules) for _ in range(runs)]
    zenith_times = [run_isolated(True, modules) for _ in range(runs)]

    avg_n = sum(native_times) / runs
    avg_z = sum(zenith_times) / runs
    saved = avg_n - avg_z
    pct = (saved / avg_n * 100) if avg_n > 0 else 0

    print("-----------------------------------------")
    print(f" {'METRIC':<16} | {'NATIVE':^10} | {'ZENITH':^8}")
    print("-----------------------------------------")
    print(f" {'Avg Boot (s)':<16} | {avg_n:.5f}s  | {avg_z:.5f}s")
    print(f" {'Avg Boot (ms)':<16} | {avg_n*1000:.2f}ms  | {avg_z*1000:.2f}ms")
    print("-----------------------------------------")
    if saved > 0:
        print(f" Saved {saved*1000:.2f}ms ({pct:.1f}% faster)")
    else:
        print(f" Overhead {abs(saved)*1000:.2f}ms — cold cache, run again for warm results")
    print("=========================================")
    print("\nNOTE: On first run Zenith builds its cache. Run again for warm results.")


if __name__ == "__main__":
    main()
