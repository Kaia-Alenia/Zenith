
import atexit
import threading
from typing import Sequence, Union, Optional, List, Dict, Any
from dataclasses import dataclass

from .core.engine import SpeculationEngine
from .core.constants import STRICT_EXCLUSIONS
from .hooks.loader import install_hook
from .speculation.predictor import ImportPredictor
from .transformer.ast_rewriter import analyze_file

__version__ = "1.2.9"
__all__ = ["ignite", "warm", "exclude", "status", "analyze", "invalidate_cache"]

_engine = SpeculationEngine()
_predictor = ImportPredictor()
_initialized = False
_init_lock = threading.Lock()

@dataclass
class IgniteConfig:
    file: Optional[str] = None
    workers: int = 4
    verbose: bool = False
    exclude: Optional[Sequence[str]] = None
    cache_path: Optional[str] = None
    show_banner: bool = True



def _print_banner() -> None:
    banner = """\033[95m
      _   _ _____ _   _ ___ _____ _   _
     / \\ | | ____| \\ | |_ _|_   _| | | |
    / _ \\| |  _| |  \\| || |  | | | |_| |
   / ___ \\ | |___| |\\  || |  | | |  _  |
  /_/   \\_\\_____|_| \\_|___|  |_| |_| |_|
         S T U D I O S   X   Z E N I T H
\033[0m"""
    print(banner)


def ignite(*args: Any, **kwargs: Any) -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        _initialized = True

    config = IgniteConfig(*args, **kwargs)

    if config.show_banner:
        _print_banner()

    if config.cache_path:
        _predictor.set_cache_path(config.cache_path)

    extra_exclusions = set(config.exclude) if config.exclude else set()

    _engine.start(workers=config.workers, verbose=config.verbose)
    _engine.add_exclusions(extra_exclusions)

    predictions = _predictor.load_predictions()
    for mod in predictions:
        _engine.preload(mod)

    install_hook(_engine, _predictor, extra_exclusions=extra_exclusions)

    if config.file:
        discovered = analyze_file(config.file)
        known = set(predictions)
        for mod in discovered:
            if mod not in known:
                _engine.preload(mod)

    atexit.register(_predictor.persist_cache)
    atexit.register(lambda: _engine.shutdown(wait=False))

    if config.verbose:
        n = len(predictions)
        print("\033[96m[Zenith] v{} | workers={} | cached={}\033[0m".format(__version__, config.workers, n))


def warm(*modules: str) -> None:
    for mod in modules:
        _engine.preload(mod)


def exclude(*modules: str) -> None:
    STRICT_EXCLUSIONS.update(modules)
    _engine.add_exclusions(set(modules))


def analyze(file: str) -> List[str]:
    return analyze_file(file)


def status() -> Dict[str, Union[str, bool, List[str]]]:
    stats = _engine.get_stats()
    return {
        "version": __version__,
        "initialized": _initialized,
        "cached_modules": _predictor.load_predictions(),
        "workers": stats.get("workers", 4),
        "preloaded_count": stats.get("preloaded_count", 0),
        "failed_count": stats.get("failed_count", 0),
        "preloaded": stats.get("preloaded", []),
        "failed": stats.get("failed", []),
    }


def invalidate_cache() -> None:
    _predictor.invalidate()
