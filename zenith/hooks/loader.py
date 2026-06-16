
import sys
import types
import importlib.abc
import importlib.machinery
import threading
from typing import Any

from zenith.core.engine import _bypass_lazy

STRICT_EXCLUSIONS = {
    "zenith", "sys", "builtins", "importlib", "_thread", "threading",
    "concurrent", "queue", "abc", "functools", "atexit", "io",
    "codecs", "encodings", "signal", "weakref", "operator", "types",
    "typing", "warnings", "traceback", "linecache", "re", "enum",
    "os", "os.path", "posixpath", "pathlib", "stat",
    "posix", "_io", "site", "ast",
}

_BOOTSTRAP_DUNDERS = {
    "__name__",
    "__spec__",
    "__loader__",
    "__path__",
    "__package__",
    "__file__",
    "__cached__",
    "__class__",
    "__dict__",
}


_obj_getattr = object.__getattribute__
_obj_setattr = object.__setattr__
_get_ident = threading.get_ident


class ZenithLazyModule(types.ModuleType):
    def __init__(
        self,
        spec: importlib.machinery.ModuleSpec,
        real_loader: importlib.abc.Loader,
        engine: Any,
        predictor: Any,
    ) -> None:
        super().__init__(spec.name)
        _obj_setattr(self, "_zenith_spec", spec)
        _obj_setattr(self, "_zenith_loader", real_loader)
        _obj_setattr(self, "_zenith_engine", engine)
        _obj_setattr(self, "_zenith_predictor", predictor)
        _obj_setattr(self, "_zenith_loaded", False)
        _obj_setattr(self, "_zenith_loading_thread", None)
        _obj_setattr(self, "_zenith_lock", threading.RLock())

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_zenith_") or name in _BOOTSTRAP_DUNDERS:
            return _obj_getattr(self, name)
        if not _obj_getattr(self, "_zenith_loaded"):
            if _obj_getattr(self, "_zenith_loading_thread") != _get_ident():
                _obj_getattr(self, "_zenith_load_module")()
        module_dict = _obj_getattr(self, "__dict__")
        if name in module_dict:
            return module_dict[name]
        return _obj_getattr(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_zenith_") or name in _BOOTSTRAP_DUNDERS:
            _obj_setattr(self, name, value)
            return
        if not _obj_getattr(self, "_zenith_loaded"):
            if _obj_getattr(self, "_zenith_loading_thread") != _get_ident():
                _obj_getattr(self, "_zenith_load_module")()
        _obj_setattr(self, name, value)

    def _zenith_load_module(self) -> None:
        if _obj_getattr(self, "_zenith_loaded"):
            return
        lock = _obj_getattr(self, "_zenith_lock")
        with lock:
            if _obj_getattr(self, "_zenith_loaded"):
                return

            _obj_setattr(self, "_zenith_loading_thread", _get_ident())
            spec = _obj_getattr(self, "_zenith_spec")
            loader = _obj_getattr(self, "_zenith_loader")
            predictor = _obj_getattr(self, "_zenith_predictor")
            engine = _obj_getattr(self, "_zenith_engine")

            import sys as _sys
            _bypass_lazy.active = True
            try:
                loader.exec_module(self)
            except Exception:
                if spec.name in _sys.modules:
                    del _sys.modules[spec.name]
                raise
            finally:
                _obj_setattr(self, "_zenith_loading_thread", None)
                _bypass_lazy.active = False

            _obj_setattr(self, "_zenith_loaded", True)
            _sys.modules[spec.name] = self

            if predictor is not None:
                predictor.save_module(spec.name)
            if engine is not None:
                engine.register_module(spec.name)

            _obj_setattr(self, "_zenith_spec", None)
            _obj_setattr(self, "_zenith_loader", None)
            _obj_setattr(self, "_zenith_engine", None)
            _obj_setattr(self, "_zenith_predictor", None)


class ZenithLazyLoader(importlib.abc.Loader):
    def __init__(
        self,
        real_loader: importlib.abc.Loader,
        engine: Any,
        predictor: Any,
    ) -> None:
        self.real_loader = real_loader
        self.engine = engine
        self.predictor = predictor

    def create_module(
        self, spec: importlib.machinery.ModuleSpec
    ) -> types.ModuleType or None:
        return ZenithLazyModule(spec, self.real_loader, self.engine, self.predictor)

    def exec_module(self, module: types.ModuleType) -> None:
        pass


class ZenithLazyFinder(importlib.abc.MetaPathFinder):
    def __init__(
        self,
        engine: Any,
        predictor: Any,
        ignored_packages: set[str] or None = None,
    ) -> None:
        self.engine = engine
        self.predictor = predictor
        self.ignored_packages = ignored_packages or STRICT_EXCLUSIONS
        self._local = threading.local()

    def find_spec(
        self,
        fullname: str,
        path: list[str or bytes] or None = None,
        target: types.ModuleType or None = None,
    ) -> importlib.machinery.ModuleSpec or None:
        if getattr(_bypass_lazy, "active", False):
            return None

        if not hasattr(self._local, "active_searches"):
            self._local.active_searches = set()

        if fullname in self._local.active_searches:
            return None

        root_pkg = fullname.split(".")[0]
        if root_pkg in self.ignored_packages:
            return None

        self._local.active_searches.add(fullname)
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
                if not isinstance(spec.loader, ZenithLazyLoader) and hasattr(
                    spec.loader, "exec_module"
                ):
                    spec.loader = ZenithLazyLoader(spec.loader, self.engine, self.predictor)
            return spec
        finally:
            self._local.active_searches.discard(fullname)


def install_hook(
    engine: Any,
    predictor: Any,
    extra_exclusions: set[str] or None = None,
) -> None:
    ignored = set(STRICT_EXCLUSIONS)
    if extra_exclusions:
        ignored.update(extra_exclusions)
    hook = ZenithLazyFinder(engine, predictor, ignored)
    sys.meta_path.insert(0, hook)