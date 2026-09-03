import pytest
from unittest.mock import patch
from zenith.benchmark import run_benchmark, BenchmarkResult

def test_run_benchmark():
    with patch("zenith.benchmark._run_target", return_value=10.0) as mock_run:
        result = run_benchmark("dummy", runs=2, warmup=1, mode="ADAPTIVE")
        assert result.mode == "ADAPTIVE"
        assert result.runs == 2
        assert result.median_time_ms == 10.0
        assert result.cache_state == "WARM"
        assert mock_run.call_count == 3  # 1 warmup + 2 runs
