from .core.engine import SpeculationEngine
from .hooks.loader import install_hook
from .speculation.predictor import predictor
import atexit

__version__ = "0.1.0"

_engine = SpeculationEngine()

def ignite():
    modulos_precarga = predictor.load_predictions()
    for mod in modulos_precarga:
        _engine.register_module(mod)
        
    install_hook(_engine, predictor)
    
    _engine.start()
    atexit.register(predictor.persist_cache)
