import pytest
import time
from zenith.config import ZenithConfig
from zenith.runtime import ZenithRuntime
from zenith.models import Mode
from zenith.exceptions import ZenithConfigurationError

def test_runtime_initialization():
    runtime = ZenithRuntime()
    assert not runtime.initialized
    
    config = ZenithConfig(mode=Mode.SAFE)
    runtime.initialize(config)
    
    assert runtime.initialized
    assert runtime.config == config
    assert runtime.start_ns is not None

def test_repeated_initialization_idempotent():
    runtime = ZenithRuntime()
    config = ZenithConfig(mode=Mode.SAFE, workers=2)
    runtime.initialize(config)
    
    # Should not raise
    runtime.initialize(config)
    assert runtime.config.workers == 2

def test_conflicting_initialization_raises():
    runtime = ZenithRuntime()
    config1 = ZenithConfig(mode=Mode.SAFE)
    config2 = ZenithConfig(mode=Mode.LAZY)
    
    runtime.initialize(config1)
    with pytest.raises(ZenithConfigurationError):
        runtime.initialize(config2)

def test_mark_ready():
    runtime = ZenithRuntime()
    runtime.initialize(ZenithConfig())
    
    assert not runtime.readiness_marked
    assert runtime.readiness_offset_ns is None
    
    # Sleep tiny bit to ensure monotonic time moves
    time.sleep(0.001)
    runtime.mark_ready()
    
    assert runtime.readiness_marked
    assert runtime.readiness_offset_ns is not None
    assert runtime.readiness_offset_ns >= 0
    
    # Should be idempotent
    prev_offset = runtime.readiness_offset_ns
    runtime.mark_ready()
    assert runtime.readiness_offset_ns == prev_offset
