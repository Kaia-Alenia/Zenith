import json
import os
import tempfile
import sys
import platform
import hashlib
from typing import Optional, Tuple
import logging
import threading

from .schema import CacheState, EnvironmentFingerprint, SCHEMA_VERSION

logger = logging.getLogger("zenith.storage")

class ZenithCache:
    def __init__(self, cache_dir: str = ".zenith"):
        self.cache_dir = cache_dir
        self.state_file = os.path.join(self.cache_dir, "state.json")
        self.lock_file = os.path.join(self.cache_dir, "lock")
        self.state = CacheState()
    
    def _compute_environment(self) -> EnvironmentFingerprint:
        return EnvironmentFingerprint(
            python_implementation=platform.python_implementation(),
            python_version=platform.python_version(),
            cache_tag=sys.implementation.cache_tag if hasattr(sys.implementation, "cache_tag") else "",
            platform=platform.system(),
            architecture=platform.machine()
        )
        
    def _compute_project_fingerprint(self) -> str:
        # Simple project root based fingerprint. In a real app we might hash pyproject.toml
        # but for performance we can just hash the CWD.
        cwd = os.getcwd()
        hasher = hashlib.sha256()
        hasher.update(cwd.encode("utf-8"))
        # Read pyproject.toml if available
        pyproject_path = os.path.join(cwd, "pyproject.toml")
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, "rb") as f:
                    hasher.update(f.read())
            except Exception:
                pass
        return hasher.hexdigest()

    def _acquire_lock(self, timeout: float = 2.0) -> bool:
        start_time = time.monotonic() if 'time' in globals() else 0
        import time
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                # O_CREAT | O_EXCL ensures atomic creation
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except FileExistsError:
                # Check for stale lock (e.g. older than 10 seconds)
                try:
                    if os.path.getmtime(self.lock_file) < time.time() - 10:
                        os.remove(self.lock_file)
                except Exception:
                    pass
                time.sleep(0.1)
            except Exception:
                return False
        return False

    def _release_lock(self):
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception:
            pass

    def load(self) -> None:
        try:
            if not os.path.exists(self.state_file):
                self._init_empty_state()
                return

            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("schema_version") != SCHEMA_VERSION:
                # Unsupported schema, init empty
                self._init_empty_state()
                return

            self.state = CacheState.from_dict(data)
            
            # Verify environment fingerprint
            current_env = self._compute_environment()
            if self.state.environment != current_env:
                # Environment changed, invalidate automatic strategy evidence but keep history if wanted
                # For safety, we wipe modules on environment mismatch to avoid bad behavior.
                self._init_empty_state()
                
        except json.JSONDecodeError:
            self._init_empty_state()
        except Exception as e:
            logger.warning(f"Cache load failed, ignoring: {e}")
            self._init_empty_state()

    def _init_empty_state(self):
        self.state = CacheState(
            schema_version=SCHEMA_VERSION,
            project_fingerprint=self._compute_project_fingerprint(),
            environment=self._compute_environment()
        )

    def persist(self) -> None:
        try:
            if not self._acquire_lock():
                logger.warning("Failed to acquire cache lock for persistence.")
                return

            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                data = self.state.to_dict()
                
                # Write to temp file then rename (atomic)
                fd, tmp_path = tempfile.mkstemp(dir=self.cache_dir, prefix="state_", suffix=".tmp")
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                
                os.replace(tmp_path, self.state_file)
            finally:
                self._release_lock()
                
        except Exception as e:
            logger.warning(f"Failed to persist cache: {e}")
