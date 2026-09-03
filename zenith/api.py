import threading
from typing import Optional

from zenith.config import ZenithConfig
from zenith.runtime import ZenithRuntime
from zenith.storage.cache import ZenithCache
from zenith.observation.runtime import RuntimeObserver
from zenith.compatibility.rules import determine_compatibility
from zenith.strategy.engine import determine_strategy
from zenith.backends.preload import PreloadBackend
from zenith.backends.loader import install_lazy_finder, uninstall_lazy_finder
from zenith.models import Strategy

_lock = threading.Lock()
_runtime = ZenithRuntime()
_cache = None
_observer = None
_preload_backend = None
_lazy_finder = None

def _should_lazy_eval(name: str) -> bool:
    global _cache, _runtime
    if not _cache or not _runtime.config:
        return False
        
    record = _cache.state.modules.get(name)
    compat = determine_compatibility(name, _runtime.config.exclude, quarantined=(record.quarantine is not None if record else False))
    decision = determine_strategy(name, record, compat, _runtime.config.mode)
    
    return decision.strategy == Strategy.LAZY

def ignite(config: Optional[ZenithConfig] = None) -> bool:
    global _cache, _observer, _preload_backend, _lazy_finder
    with _lock:
        if _runtime.config is not None:
            return False # already initialized
            
        cfg = config or ZenithConfig()
        _runtime.initialize(cfg)
        
        cache_dir = str(cfg.cache_path) if cfg.cache_path else ".zenith"
        _cache = ZenithCache(cache_dir=cache_dir)
        _cache.load()
        
        _observer = RuntimeObserver(_runtime)
        
        # Setup lazy finder
        _lazy_finder = install_lazy_finder(_should_lazy_eval)
        
        # Setup preloader
        workers = cfg.workers if cfg.workers else 4
        _preload_backend = PreloadBackend(workers=workers)
        
        # Schedule PRELOADs
        for name, record in _cache.state.modules.items():
            compat = determine_compatibility(name, cfg.exclude, quarantined=(record.quarantine is not None))
            decision = determine_strategy(name, record, compat, cfg.mode)
            if decision.strategy == Strategy.PRELOAD:
                _preload_backend.schedule(name)
                
        return True

def mark_ready() -> None:
    with _lock:
        _runtime.mark_ready()

def shutdown() -> None:
    global _cache, _preload_backend, _lazy_finder, _observer
    with _lock:
        if _lazy_finder:
            uninstall_lazy_finder(_lazy_finder)
            _lazy_finder = None
            
        if _preload_backend:
            _preload_backend.shutdown(wait=True)
            _preload_backend = None
            
        if _cache and _observer:
            # Merge runs from observer
            stats = _observer.aggregate_runs()
            from zenith.models import Phase
            from zenith.storage.schema import ModuleRecord
            import time
            run_id = str(time.time())
            
            for mod, counts in stats.items():
                if mod not in _cache.state.modules:
                    _cache.state.modules[mod] = ModuleRecord()
                rec = _cache.state.modules[mod]
                rec.runs_requested += 1
                if counts["pre"] > 0:
                    rec.pre_readiness_runs += 1
                elif counts["post"] > 0:
                    rec.post_readiness_runs += 1
                rec.last_seen_run = run_id
                
            _cache.persist()

def status() -> dict:
    with _lock:
        return {
            "mode": _runtime.config.mode.value if _runtime.config else "UNINITIALIZED",
            "uptime_ms": _runtime.get_uptime_ms(),
            "readiness_offset_ms": _runtime.get_readiness_offset_ms(),
            "cache_modules": len(_cache.state.modules) if _cache else 0
        }
