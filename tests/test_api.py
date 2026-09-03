import pytest
from zenith import ignite, mark_ready, status, ZenithConfig
from zenith.api import shutdown

def test_api_lifecycle():
    config = ZenithConfig(mode="safe")
    assert ignite(config)
    
    # Second ignite should fail/ignore
    assert not ignite(config)
    
    mark_ready()
    
    s = status()
    assert s["mode"] == "safe"
    assert s["uptime_ms"] is not None
    assert s["readiness_offset_ms"] is not None
    
    # Cleanup
    shutdown()
