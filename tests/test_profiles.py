import pytest
from zenith.analysis.profiles import merge_measurements_into_cache, merge_runtime_events_into_cache
from zenith.models import ImportMeasurement, ImportEvent, MeasurementSource, Phase
from zenith.storage.schema import CacheState

def test_merge_measurements():
    cache = CacheState()
    measurements = [
        ImportMeasurement(
            module="pandas",
            self_time_ns=500,
            cumulative_time_ns=1000,
            depth=0,
            success=True,
            source=MeasurementSource.CPYTHON_IMPORTTIME
        )
    ]
    merge_measurements_into_cache(measurements, cache)
    assert "pandas" in cache.modules
    assert cache.modules["pandas"].mean_self_import_ns == 500
    
    # Run again to test average
    measurements[0].self_time_ns = 1500
    merge_measurements_into_cache(measurements, cache)
    assert cache.modules["pandas"].mean_self_import_ns == 1000

def test_merge_runtime_events():
    cache = CacheState()
    events = [
        ImportEvent(
            module="numpy",
            monotonic_ns=0,
            phase=Phase.PRE_READINESS,
            already_loaded=False,
            importer=None,
            thread_id=1
        ),
        ImportEvent(
            module="requests",
            monotonic_ns=0,
            phase=Phase.POST_READINESS,
            already_loaded=False,
            importer=None,
            thread_id=1
        )
    ]
    
    merge_runtime_events_into_cache(events, cache, "run1")
    
    assert cache.modules["numpy"].runs_requested == 1
    assert cache.modules["numpy"].pre_readiness_runs == 1
    assert cache.modules["numpy"].post_readiness_runs == 0
    assert cache.modules["numpy"].last_seen_run == "run1"
    
    assert cache.modules["requests"].pre_readiness_runs == 0
    assert cache.modules["requests"].post_readiness_runs == 1
