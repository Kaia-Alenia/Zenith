import importlib
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from zenith.models import PreloadState, OptimizationFailure, Strategy

class PreloadBackend:
    def __init__(self, workers: int = 4):
        self.workers = workers # Just for concurrency limit if wanted, but simpler to ignore
        self.tasks: Dict[str, PreloadState] = {}
        self.failures: List[OptimizationFailure] = []
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
        
    def start(self):
        pass # Not needed
                
    def schedule(self, module: str) -> bool:
        """Schedules a preload if not already scheduled."""
        with self._lock:
            if module in self.tasks and self.tasks[module] not in (PreloadState.FAILED, PreloadState.CANCELLED):
                return False
                
            self.tasks[module] = PreloadState.SCHEDULED
            
        t = threading.Thread(target=self._execute, args=(module,), daemon=True, name=f"ZenithPreload-{module}")
        with self._lock:
            self._threads.append(t)
        t.start()
        return True
            
    def _execute(self, module: str):
        with self._lock:
            if self.tasks.get(module) == PreloadState.CANCELLED:
                return
            self.tasks[module] = PreloadState.RUNNING
            
        try:
            importlib.import_module(module)
            with self._lock:
                self.tasks[module] = PreloadState.SUCCEEDED
        except Exception as e:
            tb = traceback.format_exc()
            failure = OptimizationFailure(
                module=module,
                strategy=Strategy.PRELOAD,
                exception_type=type(e).__name__,
                message=str(e),
                monotonic_ns=time.monotonic_ns(),
                traceback_summary=tb[-1000:]
            )
            with self._lock:
                self.tasks[module] = PreloadState.FAILED
                self.failures.append(failure)
                
    def shutdown(self, wait: bool = False, timeout: Optional[float] = None):
        """Bounded shutdown."""
        with self._lock:
            for mod, state in self.tasks.items():
                if state == PreloadState.SCHEDULED:
                    self.tasks[mod] = PreloadState.CANCELLED
            threads_to_join = list(self._threads)
            self._threads.clear()
            
        if wait:
            for t in threads_to_join:
                t.join(timeout=timeout)
