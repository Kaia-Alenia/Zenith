
import sys
import threading
import importlib
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Set, List, Union

from zenith.core.constants import STRICT_EXCLUSIONS

_bypass_lazy = threading.local()


class SpeculationEngine:
    def __init__(self) -> None:
        self._executor = None
        self._preloaded = set()
        self._failed = set()
        self._lock = threading.Lock()
        self._workers = 4
        self._verbose = False
        self._exclusions = set(STRICT_EXCLUSIONS)

    def start(self, workers: int = 4, verbose: bool = False) -> None:
        self._workers = workers
        self._verbose = verbose
        self._executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="zenith-worker",
        )

    def add_exclusions(self, modules: Set[str]) -> None:
        self._exclusions.update(modules)

    def preload(self, fullname: str) -> None:
        if self._executor is None:
            return
        root = fullname.split(".")[0]
        if root in self._exclusions:
            return
        with self._lock:
            if fullname in self._preloaded or fullname in self._failed:
                return
            self._preloaded.add(fullname)
        try:
            self._executor.submit(self._load_module, fullname)
        except RuntimeError:
            with self._lock:
                self._preloaded.discard(fullname)
                self._failed.add(fullname)

    def register_module(self, fullname: str) -> None:
        self.preload(fullname)

    def _load_module(self, fullname: str) -> None:
        try:
            existing = sys.modules.get(fullname)
            if existing is not None and hasattr(existing, "_zenith_load_module"):
                existing._zenith_load_module()
                if self._verbose:
                    print("\033[92m[Zenith] Forced proxy load: {}\033[0m".format(fullname))
                return

            _bypass_lazy.active = True
            try:
                importlib.import_module(fullname)
            finally:
                _bypass_lazy.active = False

            if self._verbose:
                print("\033[92m[Zenith] Pre-loaded: {}\033[0m".format(fullname))

        except Exception:
            with self._lock:
                self._preloaded.discard(fullname)
                self._failed.add(fullname)

    def get_stats(self) -> Dict[str, Union[int, List[str]]]:
        with self._lock:
            return {
                "workers": self._workers,
                "preloaded_count": len(self._preloaded),
                "failed_count": len(self._failed),
                "preloaded": sorted(self._preloaded),
                "failed": sorted(self._failed),
            }

    def shutdown(self, wait: bool = False) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=wait)