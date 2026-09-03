import statistics
import subprocess
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    mode: str
    runs: int
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    cache_state: str

def run_benchmark(target: str, runs: int = 5, warmup: int = 1, mode: str = "SAFE") -> BenchmarkResult:
    # Warmup
    for _ in range(warmup):
        _run_target(target, mode)
        
    times: List[float] = []
    for _ in range(runs):
        elapsed = _run_target(target, mode)
        times.append(elapsed)
        
    return BenchmarkResult(
        mode=mode,
        runs=runs,
        median_time_ms=statistics.median(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        cache_state="WARM" if warmup > 0 else "COLD"
    )

def _run_target(target: str, mode: str) -> float:
    start = time.monotonic_ns()
    # Execute target in a subprocess (simplified for Phase 13)
    subprocess.run(["python", "-c", f"import {target}"], capture_output=True, check=False)
    return (time.monotonic_ns() - start) / 1_000_000
