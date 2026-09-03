import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from typing import List, Callable, Sequence
from .lazy import LazyModuleProxy, _SKIP_LAZY

class LazyMetaFinder(MetaPathFinder):
    def __init__(self, should_lazy_eval: Callable[[str], bool]):
        self.should_lazy_eval = should_lazy_eval
        
    def find_spec(self, fullname: str, path: Sequence[str] = None, target=None) -> ModuleSpec:
        if fullname in _SKIP_LAZY:
            return None
        if self.should_lazy_eval(fullname):
            # We claim it!
            return ModuleSpec(fullname, LazyLoader())
        return None

class LazyLoader(Loader):
    def create_module(self, spec: ModuleSpec):
        return LazyModuleProxy(spec.name)
        
    def exec_module(self, module):
        # We don't execute anything until resolution
        pass
        
def install_lazy_finder(should_lazy_eval: Callable[[str], bool]):
    finder = LazyMetaFinder(should_lazy_eval)
    sys.meta_path.insert(0, finder)
    return finder
    
def uninstall_lazy_finder(finder: LazyMetaFinder):
    if finder in sys.meta_path:
        sys.meta_path.remove(finder)
