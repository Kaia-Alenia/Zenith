import threading
import time
from typing import Optional, Dict
from .config import ZenithConfig
from .models import Mode, ZenithStatus, Phase
from .exceptions import ZenithConfigurationError

class ZenithRuntime:
    def __init__(self):
        self._lock = threading.Lock()
        self.config: Optional[ZenithConfig] = None
        self.initialized: bool = False
        self.readiness_marked: bool = False
        self.readiness_offset_ns: Optional[int] = None
        self.start_ns: Optional[int] = None

    def initialize(self, config: ZenithConfig) -> None:
        with self._lock:
            if self.initialized:
                # Repeated identical initialization is idempotent; conflicting raises error.
                if self.config != config:
                    raise ZenithConfigurationError("Zenith already initialized with different configuration.")
                return
            
            self.config = config
            self.start_ns = time.monotonic_ns()
            self.initialized = True
            
            # TODO: Initialize observer, knowledge_store, strategy_engine, preload_backend, lazy_backend

    def mark_ready(self) -> None:
        with self._lock:
            if not self.readiness_marked:
                self.readiness_marked = True
                if self.start_ns is not None:
                    self.readiness_offset_ns = time.monotonic_ns() - self.start_ns
                else:
                    self.readiness_offset_ns = 0

    def get_uptime_ms(self) -> int:
        with self._lock:
            if self.start_ns is None:
                return 0
            return (time.monotonic_ns() - self.start_ns) // 1_000_000

    def get_readiness_offset_ms(self) -> int:
        with self._lock:
            if self.readiness_offset_ns is None:
                return 0
            return self.readiness_offset_ns // 1_000_000

    def get_status(self) -> ZenithStatus:
        from . import __version__
        with self._lock:
            return ZenithStatus(
                version=__version__,
                mode=self.config.mode.value if self.config else Mode.SAFE.value,
                initialized=self.initialized,
                readiness_marked=self.readiness_marked,
                history_compatible_runs=0,  # TODO
                history_tracked_modules=0,  # TODO
                strategies_eager=0,         # TODO
                strategies_preload=0,       # TODO
                strategies_lazy=0,          # TODO
                strategies_protected=0,     # TODO
                backend_preload_workers=self.config.workers if self.config and self.config.workers else 0,
                backend_lazy_installed=False, # TODO
                failures_recent=0,          # TODO
                failures_quarantined=0      # TODO
            )

# Global runtime state singleton
_runtime = ZenithRuntime()
