from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

SCHEMA_VERSION = 2

@dataclass
class EnvironmentFingerprint:
    python_implementation: str
    python_version: str
    cache_tag: str
    platform: str
    architecture: str

@dataclass
class PreloadStats:
    attempts: int = 0
    successes: int = 0
    failures: int = 0

@dataclass
class LazyStats:
    attempts: int = 0
    successes: int = 0
    failures: int = 0

@dataclass
class ModuleRecord:
    runs_requested: int = 0
    pre_readiness_runs: int = 0
    post_readiness_runs: int = 0
    mean_self_import_ns: Optional[int] = None
    mean_cumulative_import_ns: Optional[int] = None
    last_seen_run: Optional[str] = None
    compatibility: str = "UNKNOWN"
    quarantine: Optional[str] = None
    preload: PreloadStats = field(default_factory=PreloadStats)
    lazy: LazyStats = field(default_factory=LazyStats)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "runs_requested": self.runs_requested,
            "pre_readiness_runs": self.pre_readiness_runs,
            "post_readiness_runs": self.post_readiness_runs,
            "mean_self_import_ns": self.mean_self_import_ns,
            "mean_cumulative_import_ns": self.mean_cumulative_import_ns,
            "last_seen_run": self.last_seen_run,
            "compatibility": self.compatibility,
            "quarantine": self.quarantine,
            "preload": {
                "attempts": self.preload.attempts,
                "successes": self.preload.successes,
                "failures": self.preload.failures,
            },
            "lazy": {
                "attempts": self.lazy.attempts,
                "successes": self.lazy.successes,
                "failures": self.lazy.failures,
            }
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleRecord":
        return cls(
            runs_requested=data.get("runs_requested", 0),
            pre_readiness_runs=data.get("pre_readiness_runs", 0),
            post_readiness_runs=data.get("post_readiness_runs", 0),
            mean_self_import_ns=data.get("mean_self_import_ns"),
            mean_cumulative_import_ns=data.get("mean_cumulative_import_ns"),
            last_seen_run=data.get("last_seen_run"),
            compatibility=data.get("compatibility", "UNKNOWN"),
            quarantine=data.get("quarantine"),
            preload=PreloadStats(**data.get("preload", {})),
            lazy=LazyStats(**data.get("lazy", {})),
        )

@dataclass
class CacheState:
    schema_version: int = SCHEMA_VERSION
    project_fingerprint: str = ""
    environment: Optional[EnvironmentFingerprint] = None
    modules: Dict[str, ModuleRecord] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project": {
                "fingerprint": self.project_fingerprint
            },
            "environment": {
                "python_implementation": self.environment.python_implementation if self.environment else "",
                "python_version": self.environment.python_version if self.environment else "",
                "cache_tag": self.environment.cache_tag if self.environment else "",
                "platform": self.environment.platform if self.environment else "",
                "architecture": self.environment.architecture if self.environment else ""
            },
            "modules": {k: v.to_dict() for k, v in self.modules.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheState":
        env_data = data.get("environment", {})
        env = EnvironmentFingerprint(
            python_implementation=env_data.get("python_implementation", ""),
            python_version=env_data.get("python_version", ""),
            cache_tag=env_data.get("cache_tag", ""),
            platform=env_data.get("platform", ""),
            architecture=env_data.get("architecture", "")
        )
        project_data = data.get("project", {})
        
        modules = {}
        for k, v in data.get("modules", {}).items():
            modules[k] = ModuleRecord.from_dict(v)
            
        return cls(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            project_fingerprint=project_data.get("fingerprint", ""),
            environment=env,
            modules=modules
        )
