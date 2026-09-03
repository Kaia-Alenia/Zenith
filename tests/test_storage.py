import pytest
import os
import tempfile
import json
from zenith.storage import ZenithCache, CacheState, ModuleRecord

def test_cache_init_empty(tmp_path):
    cache_dir = tmp_path / ".zenith"
    cache = ZenithCache(cache_dir=str(cache_dir))
    cache.load()
    assert cache.state.schema_version == 2
    assert cache.state.environment is not None
    assert cache.state.project_fingerprint != ""

def test_cache_persist_and_load(tmp_path):
    cache_dir = tmp_path / ".zenith"
    cache = ZenithCache(cache_dir=str(cache_dir))
    cache.load()
    
    # Modify state
    cache.state.modules["pandas"] = ModuleRecord(runs_requested=5, compatibility="SAFE")
    cache.persist()
    
    # Reload
    cache2 = ZenithCache(cache_dir=str(cache_dir))
    cache2.load()
    
    assert "pandas" in cache2.state.modules
    assert cache2.state.modules["pandas"].runs_requested == 5
    assert cache2.state.modules["pandas"].compatibility == "SAFE"

def test_cache_handles_corruption_gracefully(tmp_path):
    cache_dir = tmp_path / ".zenith"
    cache_dir.mkdir()
    state_file = cache_dir / "state.json"
    state_file.write_text("{bad_json...")
    
    cache = ZenithCache(cache_dir=str(cache_dir))
    # Should not raise exception
    cache.load()
    
    # Should initialize empty
    assert len(cache.state.modules) == 0

def test_cache_handles_schema_mismatch(tmp_path):
    cache_dir = tmp_path / ".zenith"
    cache_dir.mkdir()
    state_file = cache_dir / "state.json"
    state_file.write_text(json.dumps({"schema_version": 1, "modules": {"pandas": {}}}))
    
    cache = ZenithCache(cache_dir=str(cache_dir))
    cache.load()
    
    # Should initialize empty
    assert len(cache.state.modules) == 0

def test_cache_environment_mismatch(tmp_path):
    cache_dir = tmp_path / ".zenith"
    cache = ZenithCache(cache_dir=str(cache_dir))
    cache.load()
    cache.state.modules["pandas"] = ModuleRecord(runs_requested=5, compatibility="SAFE")
    cache.persist()
    
    # Simulate environment change
    cache2 = ZenithCache(cache_dir=str(cache_dir))
    
    original_compute = cache2._compute_environment
    def mock_compute():
        env = original_compute()
        env.python_version = "9.9.9" # Fake change
        return env
        
    cache2._compute_environment = mock_compute
    cache2.load()
    
    # Modules should be cleared because environment changed
    assert len(cache2.state.modules) == 0
