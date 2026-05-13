from .core.engine import SpeculationEngine
from .hooks.loader import install_hook
from .speculation.predictor import predictor
import atexit
import functools

__version__ = "0.1.5"

_engine = SpeculationEngine()

@functools.lru_cache(maxsize=1)
def ignite():
    banner = """\033[95m
      _   _ _____ _   _ ___ _____ _   _ 
     / \\ | | ____| \\ | |_ _|_   _| | | |
    / _ \\| |  _| |  \\| || |  | | | |_| |
   / ___ \\ | |___| |\\  || |  | | |  _  |
  /_/   \\_\\_____|_| \\_|___|  |_| |_| |_|
         S T U D I O S   X   Z E N I T H
\033[0m"""
    print(banner)

    preload_modules = predictor.load_predictions()
    for mod in preload_modules:
        _engine.register_module(mod)
        
    install_hook(_engine, predictor)
    
    _engine.start()
    atexit.register(predictor.persist_cache)
