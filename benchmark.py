import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def run_isolated(use_zenith: bool, modules: list[str]) -> float:
    mod_list = repr(modules)
    header = "import zenith; zenith.ignite(show_banner=False)\n" if use_zenith else ""
    code = f"""
import sys, time
sys.path.insert(0, {repr(str(ROOT))})
{header}
start = time.perf_counter()
for m in {mod_list}:
    __import__(m)
print(time.perf_counter() - start)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "traditional"
    modules = ["json", "sqlite3", "urllib.request", "xml.etree.ElementTree", "multiprocessing"]

    if mode == "--zenith":
        t = run_isolated(True, modules)
        print(f"Boot WITH Zenith   : {t:.5f}s  ({t*1000:.2f}ms)")
    else:
        t = run_isolated(False, modules)
        print(f"Boot WITHOUT Zenith: {t:.5f}s  ({t*1000:.2f}ms)")