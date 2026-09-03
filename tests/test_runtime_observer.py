import pytest
import time
from zenith.observation.runtime import RuntimeObserver
from zenith.runtime import ZenithRuntime
from zenith.config import ZenithConfig
from zenith.models import Phase

def test_runtime_observer_phases():
    runtime = ZenithRuntime()
    config = ZenithConfig(early_process_window=0.1)
    runtime.initialize(config)
    
    observer = RuntimeObserver(runtime)
    
    # Record event in pre-readiness window
    observer.record_import("module_a", already_loaded=False)
    
    # Sleep to exceed heuristic window
    time.sleep(0.15)
    observer.record_import("module_b", already_loaded=False)
    
    # Mark explicit readiness
    runtime.mark_ready()
    observer.record_import("module_c", already_loaded=False)
    
    events = observer.get_events()
    assert len(events) == 3
    
    assert events[0].module == "module_a"
    assert events[0].phase == Phase.PRE_READINESS
    
    assert events[1].module == "module_b"
    assert events[1].phase == Phase.POST_READINESS
    
    assert events[2].module == "module_c"
    assert events[2].phase == Phase.POST_READINESS

def test_observer_aggregation():
    runtime = ZenithRuntime()
    runtime.initialize(ZenithConfig())
    observer = RuntimeObserver(runtime)
    
    observer.record_import("mod1", already_loaded=False)
    observer.record_import("mod1", already_loaded=True)
    
    runtime.mark_ready()
    observer.record_import("mod1", already_loaded=True)
    observer.record_import("mod2", already_loaded=False)
    
    stats = observer.aggregate_runs()
    
    assert "mod1" in stats
    assert stats["mod1"]["pre"] == 2
    assert stats["mod1"]["post"] == 1
    
    assert "mod2" in stats
    assert stats["mod2"]["pre"] == 0
    assert stats["mod2"]["post"] == 1
