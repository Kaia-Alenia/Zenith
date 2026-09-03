from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

class Mode(Enum):
    PROFILE = "profile"
    SAFE = "safe"
    LAZY = "lazy"
    ADAPTIVE = "adaptive"

class Strategy(Enum):
    EAGER = "eager"
    PRELOAD = "preload"
    LAZY = "lazy"
    PROTECTED = "protected"
    UNKNOWN = "unknown"

class Compatibility(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    UNSUPPORTED = "unsupported"
    PROTECTED = "protected"
    QUARANTINED = "quarantined"

class Phase(Enum):
    PRE_READINESS = "pre_readiness"
    POST_READINESS = "post_readiness"

class MeasurementSource(Enum):
    CPYTHON_IMPORTTIME = "cpython_importtime"
    RUNTIME_OBSERVER = "runtime_observer"
    STATIC_ANALYSIS = "static_analysis"
    BENCHMARK = "benchmark"

class PreloadState(Enum):
    NOT_SCHEDULED = "not_scheduled"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class ImportEvent:
    module: str
    monotonic_ns: int
    phase: Phase
    already_loaded: bool
    importer: Optional[str]
    thread_id: int

@dataclass
class ImportMeasurement:
    module: str
    self_time_ns: Optional[int]
    cumulative_time_ns: Optional[int]
    depth: Optional[int]
    success: bool
    source: MeasurementSource

@dataclass
class ZenithStatus:
    version: str
    mode: str
    initialized: bool
    readiness_marked: bool
    history_compatible_runs: int
    history_tracked_modules: int
    strategies_eager: int
    strategies_preload: int
    strategies_lazy: int
    strategies_protected: int
    backend_preload_workers: int
    backend_lazy_installed: bool
    failures_recent: int
    failures_quarantined: int

@dataclass
class OptimizationFailure:
    module: str
    strategy: Strategy
    exception_type: str
    message: str
    monotonic_ns: int
    traceback_summary: Optional[str]

@dataclass
class StrategyDecision:
    module: str
    strategy: Strategy
    confidence: float
    reasons: List[str]
    evidence_runs: int
