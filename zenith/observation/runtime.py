import time
import threading
from typing import List, Optional
from zenith.models import ImportEvent, Phase
from zenith.runtime import ZenithRuntime

class RuntimeObserver:
    def __init__(self, runtime: ZenithRuntime):
        self.runtime = runtime
        self._events: List[ImportEvent] = []
        self._lock = threading.Lock()
        
    def record_import(self, module: str, already_loaded: bool, importer: Optional[str] = None):
        """Records an import event without changing import semantics."""
        now_ns = time.monotonic_ns()
        
        # Determine phase based on readiness
        # If readiness has been marked, it's POST_READINESS.
        # Otherwise, check early_process_window.
        
        phase = Phase.PRE_READINESS
        
        if self.runtime.readiness_marked:
            if self.runtime.readiness_offset_ns is not None:
                # Event happened after readiness
                phase = Phase.POST_READINESS
        else:
            # Fallback to heuristic
            if self.runtime.start_ns is not None and self.runtime.config is not None:
                elapsed_s = (now_ns - self.runtime.start_ns) / 1e9
                if elapsed_s > self.runtime.config.early_process_window:
                    phase = Phase.POST_READINESS
                    
        event = ImportEvent(
            module=module,
            monotonic_ns=now_ns,
            phase=phase,
            already_loaded=already_loaded,
            importer=importer,
            thread_id=threading.get_ident()
        )
        
        with self._lock:
            self._events.append(event)
            
    def get_events(self) -> List[ImportEvent]:
        with self._lock:
            return list(self._events)
            
    def aggregate_runs(self) -> dict:
        """Aggregates events into module run statistics"""
        stats = {}
        with self._lock:
            for event in self._events:
                if event.module not in stats:
                    stats[event.module] = {"pre": 0, "post": 0}
                    
                if event.phase == Phase.PRE_READINESS:
                    stats[event.module]["pre"] += 1
                else:
                    stats[event.module]["post"] += 1
        return stats
