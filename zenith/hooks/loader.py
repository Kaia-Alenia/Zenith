import sys
import types
import importlib.abc
import importlib.machinery
from typing import Any

STRICT_EXCLUSIONS = {"zenith", "sys", "builtins", "importlib", "nerve"}

class ZenithLazyModule(types.ModuleType):
    def __init__(self, spec: importlib.machinery.ModuleSpec, real_loader: importlib.abc.Loader, engine: Any, predictor: Any) -> None:
        super().__init__(spec.name)
        object.__setattr__(self, "_zenith_spec", spec)
        object.__setattr__(self, "_zenith_loader", real_loader)
        object.__setattr__(self, "_zenith_engine", engine)
        object.__setattr__(self, "_zenith_predictor", predictor)
        object.__setattr__(self, "_zenith_loaded", False)

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_zenith_") or (name.startswith("__") and name.endswith("__")):
            return object.__getattribute__(self, name)
        
        object.__getattribute__(self, "_zenith_load_module")()
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_zenith_") or (name.startswith("__") and name.endswith("__")):
            object.__setattr__(self, name, value)
            return
        
        object.__getattribute__(self, "_zenith_load_module")()
        object.__setattr__(self, name, value)

    def _zenith_load_module(self) -> None:
        if object.__getattribute__(self, "_zenith_loaded"):
            return

        spec = object.__getattribute__(self, "_zenith_spec")
        loader = object.__getattribute__(self, "_zenith_loader")
        engine = object.__getattribute__(self, "_zenith_engine")
        predictor = object.__getattribute__(self, "_zenith_predictor")

        if predictor is not None:
            predictor.save_module(spec.name)
        if engine is not None:
            engine.register_module(spec.name)

        loader.exec_module(self)
        object.__setattr__(self, "_zenith_loaded", True)


class ZenithLazyLoader(importlib.abc.Loader):
    def __init__(self, real_loader: importlib.abc.Loader, engine: Any, predictor: Any) -> None:
        self.real_loader = real_loader
        self.engine = engine
        self.predictor = predictor

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> types.ModuleType | None:
        return ZenithLazyModule(spec, self.real_loader, self.engine, self.predictor)

    def exec_module(self, module: types.ModuleType) -> None:
        pass


class ZenithLazyFinder(importlib.abc.MetaPathFinder):
    _active_searches: set[str] = set()

    def __init__(self, engine: Any, predictor: Any, ignored_packages: set[str] | None = None) -> None:
        self.engine = engine
        self.predictor = predictor
        self.original_finders = sys.meta_path.copy()
        self.ignored_packages: set[str] = ignored_packages or STRICT_EXCLUSIONS

    def find_spec(
        self,
        fullname: str,
        path: list[str | bytes] | None = None,
        target: types.ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname in self._active_searches:
            return None

        root_pkg = fullname.split(".")[0]
        if root_pkg in self.ignored_packages:
            return None

        self._active_searches.add(fullname)
        try:
            spec = None
            for finder in sys.meta_path:
                if finder is self:
                    continue
                try:
                    spec = finder.find_spec(fullname, path, target)
                    if spec is not None:
                        break
                except Exception:
                    continue

            if spec is not None and spec.loader is not None:
                if not isinstance(spec.loader, ZenithLazyLoader) and hasattr(spec.loader, "exec_module"):
                    spec.loader = ZenithLazyLoader(spec.loader, self.engine, self.predictor)
                    if self.predictor is not None:
                        self.predictor.save_module(fullname)
            return spec
        finally:
            self._active_searches.discard(fullname)


def install_hook(engine: Any, predictor: Any) -> None:
    hook = ZenithLazyFinder(engine, predictor)
    sys.meta_path.insert(0, hook)
