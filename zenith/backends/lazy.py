import sys
import importlib
from typing import Any, Callable

_SKIP_LAZY = set()

class LazyModuleProxy:
    def __init__(self, name: str):
        self.__name__ = name
        self.__module = None
        self.__resolving = False
    def __resolve(self):
        if self.__module is not None:
            return self.__module
            
        if self.__resolving:
            raise ImportError(f"Circular dependency detected while resolving lazy module {self.__name__}")
            
        self.__resolving = True
        try:
            if sys.modules.get(self.__name__) is self:
                del sys.modules[self.__name__]
                
            _SKIP_LAZY.add(self.__name__)
            try:
                self.__module = importlib.import_module(self.__name__)
            finally:
                _SKIP_LAZY.discard(self.__name__)
        finally:
            self.__resolving = False
            
        return self.__module

    def __getattr__(self, item: str) -> Any:
        # Avoid resolving for typing/inspection during static analysis if possible
        if item in ("__path__", "__file__", "__spec__"):
            # A bit of a hack: if someone asks for these, resolve it,
            # but sometimes IDEs ask without wanting to trigger a full load.
            # We'll just resolve for everything for now except special typing fields
            pass
            
        module = self.__resolve()
        return getattr(module, item)

    def __setattr__(self, key: str, value: Any):
        if key in ("__name__", "_LazyModuleProxy__module", "_LazyModuleProxy__resolving"):
            super().__setattr__(key, value)
        else:
            module = self.__resolve()
            setattr(module, key, value)

    def __dir__(self):
        module = self.__resolve()
        return dir(module)
