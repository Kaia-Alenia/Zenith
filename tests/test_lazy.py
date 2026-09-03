import pytest
import sys
from zenith.backends.loader import install_lazy_finder, uninstall_lazy_finder

def test_lazy_proxy():
    # Install for a dummy module
    def should_lazy(name):
        return name == "dummy_lazy_module"
        
    finder = install_lazy_finder(should_lazy)
    try:
        # Create a dummy module file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def hello(): return 'world'\nx = 42\nclass MyBase: pass")
            temp_name = f.name
            
        sys.path.insert(0, os.path.dirname(temp_name))
        mod_name = os.path.basename(temp_name)[:-3]
        
        # Make the finder intercept it
        finder.should_lazy_eval = lambda n: n == mod_name
        
        # Import it
        import importlib
        mod = importlib.import_module(mod_name)
        
        # It should be a proxy
        from zenith.backends.lazy import LazyModuleProxy
        assert isinstance(mod, LazyModuleProxy)
        
        # Accessing an attribute resolves it
        assert mod.hello() == "world"
        assert mod.x == 42
        
        # Inheritance
        class Derived(mod.MyBase):
            pass
            
        d = Derived()
        assert isinstance(d, mod.MyBase)
        
    finally:
        uninstall_lazy_finder(finder)
        sys.path.pop(0)
        try:
            os.remove(temp_name)
        except Exception:
            pass
