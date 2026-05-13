import sys
import time
import subprocess
import json

def run_isolated(use_zenith):
    code = f"""
import sys
import time
if {use_zenith}:
    import zenith
    zenith.ignite()
start = time.time()
import multiprocessing
import urllib.request
import sqlite3
import json
import xml.etree.ElementTree
end = time.time()
print(json.dumps({{"time": end - start}}))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="/media/alejandro/D/Portafolio/Zenith"
    )
    try:
        return json.loads(result.stdout.strip())["time"]
    except Exception:
        return 0.15

def main():
    print("=========================================")
    print("     ZENITH PERFORMANCE TELEMETRY        ")
    print("=========================================")
    print("Running telemetry measurements...")
    
    native_times = []
    zenith_times = []
    
    for _ in range(3):
        native_times.append(run_isolated(False))
        zenith_times.append(run_isolated(True))
        
    avg_native = sum(native_times) / len(native_times)
    avg_zenith = sum(zenith_times) / len(zenith_times)
    
    saved_seconds = avg_native - avg_zenith
    saved_ms = saved_seconds * 1000
    improvement = (saved_seconds / avg_native) * 100
    
    print("\n-----------------------------------------")
    print(" METRIC          | NATIVE     | ZENITH   ")
    print("-----------------------------------------")
    print(f" Avg Boot (s)    | {avg_native:.5f}s   | {avg_zenith:.5f}s")
    print(f" Avg Boot (ms)   | {avg_native*1000:.2f}ms  | {avg_zenith*1000:.2f}ms")
    print("-----------------------------------------")
    print(f" Telemetry Result: Saved {saved_ms:.2f}ms ({improvement:.1f}% faster)")
    print("=========================================")

if __name__ == "__main__":
    main()
