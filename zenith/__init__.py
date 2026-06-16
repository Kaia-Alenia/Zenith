# ALENIA STUDIOS TOOL LICENSE Version 1.0 Copyright (c) 2026 Alenia Studios This tool is designed to be free and accessible for the indie developer community. By using this software, you agree to the following terms: 1. OUTPUT OWNERSHIP & USE: The audio, video, or data files processed by this Software remain 100% your property. No attribution to Alenia Studios is required in your final project for simply using this tool to process your files. 2. ALWAYS FREE & SPREAD THE WORD: This Software is completely free for commercial and non-commercial projects. If you find it useful, we strongly encourage you to recommend it to other developers. 3. CODE ATTRIBUTION: If you modify, fork, or distribute the source code of this Software, you must provide appropriate credit to Alenia Studios and the respective community translators. 4. NO RESALE: Standalone redistribution, sublicensing, or resale of this Software or its source code for profit is strictly prohibited. It must remain free. 5. NO AI TRAINING: The source code, documentation, and logic of this Software may not be used, scraped, or included in datasets for the training of Artificial Intelligence models or machine learning algorithms. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import atexit
import threading
from typing import Sequence, Union, Optional, List, Dict

from .core.engine import SpeculationEngine
from .hooks.loader import install_hook, STRICT_EXCLUSIONS
from .speculation.predictor import ImportPredictor
from .transformer.ast_rewriter import analyze_file

__version__ = "1.2.5"
__all__ = ["ignite", "warm", "exclude", "status", "analyze", "invalidate_cache"]

_engine = SpeculationEngine()
_predictor = ImportPredictor()
_initialized = False
_init_lock = threading.Lock()


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


def ignite(
    file: Optional[str] = None,
    workers: int = 4,
    verbose: bool = False,
    exclude: Optional[Sequence[str]] = None,
    cache_path: Optional[str] = None,
    show_banner: bool = True,
) -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        _initialized = True

    if show_banner:
        _print_banner()

    if cache_path:
        _predictor.set_cache_path(cache_path)

    extra_exclusions = set(exclude) if exclude else set()

    _engine.start(workers=workers, verbose=verbose)
    _engine.add_exclusions(extra_exclusions)

    predictions = _predictor.load_predictions()
    for mod in predictions:
        _engine.preload(mod)

    install_hook(_engine, _predictor, extra_exclusions=extra_exclusions)

    if file:
        discovered = analyze_file(file)
        known = set(predictions)
        for mod in discovered:
            if mod not in known:
                _engine.preload(mod)

    atexit.register(_predictor.persist_cache)
    atexit.register(lambda: _engine.shutdown(wait=False))

    if verbose:
        n = len(predictions)
        print("\033[96m[Zenith] v{} | workers={} | cached={}\033[0m".format(__version__, workers, n))


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
