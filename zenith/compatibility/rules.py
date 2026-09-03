import sys
import importlib.util
from typing import Sequence
from zenith.models import Compatibility

HARD_PROTECTED = {
    "zenith",
    "sys",
    "builtins",
    "importlib",
    "_imp",
    "_io",
    "os",
    "site"
}

def determine_compatibility(
    module_name: str, 
    user_excludes: Sequence[str] = (),
    quarantined: bool = False
) -> Compatibility:
    """
    Evaluates the compatibility classification for a module.
    """
    if quarantined:
        return Compatibility.QUARANTINED
        
    root_module = module_name.split(".")[0]
    
    if root_module in HARD_PROTECTED or module_name in HARD_PROTECTED:
        return Compatibility.PROTECTED
        
    if root_module in user_excludes or module_name in user_excludes:
        return Compatibility.PROTECTED
        
    # Check if built-in or frozen
    if module_name in sys.builtin_module_names:
        return Compatibility.PROTECTED
        
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            # Can't find it statically, might be dynamic.
            # We can't guarantee safety.
            return Compatibility.CAUTION
            
        # Extension modules (.so, .pyd, ExtensionFileLoader) are CAUTION
        loader_name = type(spec.loader).__name__
        if loader_name == "ExtensionFileLoader":
            return Compatibility.CAUTION
            
        # Standard SourceFileLoader / SourcelessFileLoader / Namespace
        return Compatibility.SAFE
        
    except Exception:
        # If finding spec raises, be safe
        return Compatibility.CAUTION
