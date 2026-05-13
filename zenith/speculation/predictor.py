from pathlib import Path
import json
import threading
from typing import List

CACHE_FILE = Path(".zenith_cache.json")

class ImportPredictor:
    def __init__(self) -> None:
        self.history = set()
        self.lock = threading.Lock()
    
    def load_predictions(self) -> List[str]:
        if CACHE_FILE.exists():
            try:
                with CACHE_FILE.open("r", encoding="utf-8") as f:
                    datos = json.load(f)
                    return datos.get("modulos", [])
            except Exception:
                return []
        return []

    def save_module(self, fullname: str) -> None:
        with self.lock:
            self.history.add(fullname)
        
    def persist_cache(self) -> None:
        try:
            with self.lock:
                modulos_guardados = set(self.load_predictions())
                modulos_totales = list(modulos_guardados.union(self.history))
            
            with CACHE_FILE.open("w", encoding="utf-8") as f:
                json.dump({"modulos": modulos_totales}, f, indent=4)
        except Exception:
            pass

predictor = ImportPredictor()
