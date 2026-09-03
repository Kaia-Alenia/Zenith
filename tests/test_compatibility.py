import pytest
from zenith.compatibility import determine_compatibility, HARD_PROTECTED
from zenith.models import Compatibility

def test_compatibility_quarantine():
    assert determine_compatibility("pandas", quarantined=True) == Compatibility.QUARANTINED

def test_compatibility_hard_protected():
    for p in HARD_PROTECTED:
        assert determine_compatibility(p) == Compatibility.PROTECTED
        assert determine_compatibility(f"{p}.submodule") == Compatibility.PROTECTED

def test_compatibility_user_excludes():
    assert determine_compatibility("django", user_excludes=["django"]) == Compatibility.PROTECTED

def test_compatibility_builtins():
    import sys
    # Pick a known builtin module
    builtin_mod = sys.builtin_module_names[0]
    assert determine_compatibility(builtin_mod) == Compatibility.PROTECTED

def test_compatibility_safe():
    # A standard pure python module from stdlib
    assert determine_compatibility("json") == Compatibility.SAFE

def test_compatibility_unknown():
    # If module cannot be found, it returns CAUTION
    assert determine_compatibility("some_non_existent_module_12345") == Compatibility.CAUTION
