import pytest
import tempfile
from zenith.analysis.static import analyze_file

def test_analyze_file_imports():
    source = """
import os
import sys as system

def my_func():
    import json
    
if TYPE_CHECKING:
    from typing import List
    
importlib.import_module("dynamic_mod")
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(source)
        temp_name = f.name
        
    try:
        result = analyze_file(temp_name)
        assert result.filepath == temp_name
        assert len(result.imports) == 5
        
        # import os
        assert result.imports[0].module == "os"
        assert not result.imports[0].is_nested
        assert not result.imports[0].is_dynamic_call
        
        # import sys as system
        assert result.imports[1].module == "sys"
        assert result.imports[1].alias == "system"
        
        # import json (nested)
        assert result.imports[2].module == "json"
        assert result.imports[2].is_nested
        
        # from typing import List
        assert result.imports[3].module == "typing.List"
        assert result.imports[3].context == "TYPE_CHECKING"
        
        # importlib.import_module
        assert result.imports[4].module == "<dynamic>"
        assert result.imports[4].is_dynamic_call
        
    finally:
        import os
        os.remove(temp_name)
