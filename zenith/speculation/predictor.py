
import json
import os
import tempfile
import threading
import logging
from pathlib import Path
from typing import List, Optional

_DEFAULT_CACHE = ".zenith_cache.json"

logger = logging.getLogger(__name__)


class ImportPredictor:
    def __init__(self, cache_path: Optional[str] = None) -> None:
        self.history = set()
        self.lock = threading.RLock()
        self._cache_path = Path(cache_path or _DEFAULT_CACHE)
        self._loaded_predictions = None

    def set_cache_path(self, path: str) -> None:
        with self.lock:
            self._cache_path = Path(path)
            self._loaded_predictions = None

    def load_predictions(self) -> List[str]:
        with self.lock:
            if self._loaded_predictions is not None:
                return self._loaded_predictions
            if not self._cache_path.exists():
                self._loaded_predictions = []
                return []
            try:
                with self._cache_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    self._loaded_predictions = []
                    return []
                modules = data.get("modules", [])
                self._loaded_predictions = [m for m in modules if isinstance(m, str) and m.strip()]
                return self._loaded_predictions
            except Exception as e:
                logger.warning("Failed to load predictions: %s", e)
                self._loaded_predictions = []
                return []

    def save_module(self, fullname: str) -> None:
        with self.lock:
            self.history.add(fullname)

    def persist_cache(self) -> None:
        try:
            with self.lock:
                self._loaded_predictions = None
                saved = set(self.load_predictions())
                merged = list(saved.union(self.history))
                self._cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                fd, temp_path_str = tempfile.mkstemp(
                    dir=self._cache_path.parent,
                    prefix=self._cache_path.name + "-",
                    suffix=".tmp"
                )
                temp_path = Path(temp_path_str)
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump({"modules": sorted(merged)}, f, indent=4)
                    temp_path.replace(self._cache_path)
                except Exception:
                    if temp_path.exists():
                        temp_path.unlink()
                    raise
                
                self._loaded_predictions = sorted(merged)
        except Exception as e:
            logger.warning("Failed to persist cache: %s", e)

    def invalidate(self) -> None:
        try:
            with self.lock:
                self._loaded_predictions = None
                self.history.clear()
                if self._cache_path.exists():
                    self._cache_path.unlink()
        except Exception as e:
            logger.warning("Failed to invalidate cache: %s", e)


predictor = ImportPredictor()
