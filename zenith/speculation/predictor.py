# ALENIA STUDIOS TOOL LICENSE Version 1.0 Copyright (c) 2026 Alenia Studios This tool is designed to be free and accessible for the indie developer community. By using this software, you agree to the following terms: 1. OUTPUT OWNERSHIP & USE: The audio, video, or data files processed by this Software remain 100% your property. No attribution to Alenia Studios is required in your final project for simply using this tool to process your files. 2. ALWAYS FREE & SPREAD THE WORD: This Software is completely free for commercial and non-commercial projects. If you find it useful, we strongly encourage you to recommend it to other developers. 3. CODE ATTRIBUTION: If you modify, fork, or distribute the source code of this Software, you must provide appropriate credit to Alenia Studios and the respective community translators. 4. NO RESALE: Standalone redistribution, sublicensing, or resale of this Software or its source code for profit is strictly prohibited. It must remain free. 5. NO AI TRAINING: The source code, documentation, and logic of this Software may not be used, scraped, or included in datasets for the training of Artificial Intelligence models or machine learning algorithms. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import json
import threading
from pathlib import Path
from typing import List, Optional

_DEFAULT_CACHE = ".zenith_cache.json"


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
            except Exception:
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
                temp_path = self._cache_path.with_suffix(".tmp")
                with temp_path.open("w", encoding="utf-8") as f:
                    json.dump({"modules": sorted(merged)}, f, indent=4)
                temp_path.replace(self._cache_path)
                self._loaded_predictions = sorted(merged)
        except Exception:
            pass

    def invalidate(self) -> None:
        try:
            with self.lock:
                self._loaded_predictions = None
                self.history.clear()
                if self._cache_path.exists():
                    self._cache_path.unlink()
        except Exception:
            pass


predictor = ImportPredictor()
