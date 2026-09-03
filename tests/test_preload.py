import pytest
import time
from zenith.backends.preload import PreloadBackend
from zenith.models import PreloadState

def test_preload_success():
    backend = PreloadBackend(workers=1)
    import importlib
    original_import = importlib.import_module
    importlib.import_module = lambda m: m
    try:
        assert backend.schedule("json")
        timeout = time.time() + 5
        while time.time() < timeout:
            if backend.tasks.get("json") in (PreloadState.SUCCEEDED, PreloadState.FAILED):
                break
            time.sleep(0.01)
        assert backend.tasks["json"] == PreloadState.SUCCEEDED
    finally:
        importlib.import_module = original_import
        backend.shutdown(wait=True)

def test_preload_failure():
    backend = PreloadBackend(workers=1)
    import importlib
    original_import = importlib.import_module
    def mock_import(name):
        raise ModuleNotFoundError(f"No module named '{name}'")
    importlib.import_module = mock_import
    try:
        assert backend.schedule("non_existent_module_for_test")
        timeout = time.time() + 5
        while time.time() < timeout:
            if backend.tasks.get("non_existent_module_for_test") in (PreloadState.SUCCEEDED, PreloadState.FAILED):
                break
            time.sleep(0.01)
            
        assert backend.tasks["non_existent_module_for_test"] == PreloadState.FAILED
        assert len(backend.failures) == 1
        assert backend.failures[0].module == "non_existent_module_for_test"
        assert backend.failures[0].exception_type == "ModuleNotFoundError"
    finally:
        importlib.import_module = original_import
        backend.shutdown(wait=True)

def test_preload_duplicate_scheduling():
    backend = PreloadBackend(workers=1)
    try:
        assert backend.schedule("os")
        assert not backend.schedule("os")
    finally:
        backend.shutdown(wait=True)

if __name__ == '__main__':
    print("Running success...")
    test_preload_success()
    print("Running failure...")
    test_preload_failure()
    print("Running duplicate...")
    test_preload_duplicate_scheduling()
    print("All passed!")
