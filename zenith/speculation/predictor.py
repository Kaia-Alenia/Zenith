from pathlib import Path
import json
import threading

CACHE_FILE = Path(".zenith_cache.json")

class ImportPredictor:
    def __init__(self) -> None:
        self.history = set()
        self.lock = threading.Lock()
    
    def load_predictions(self) -> list[str]:
        if CACHE_FILE.exists():
            try:
                with CACHE_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("modules", [])
            except Exception:
                return []
        return []

    def save_module(self, fullname: str) -> None:
        with self.lock:
            self.history.add(fullname)
        
    def persist_cache(self) -> None:
        try:
            with self.lock:
                saved_modules = set(self.load_predictions())
                total_modules = list(saved_modules.union(self.history))
            
            with CACHE_FILE.open("w", encoding="utf-8") as f:
                json.dump({"modules": total_modules}, f, indent=4)
        except Exception:
            pass

predictor = ImportPredictor()
