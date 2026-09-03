import pytest
from zenith.strategy.engine import determine_strategy
from zenith.models import Strategy, Compatibility, Mode
from zenith.storage.schema import ModuleRecord, PreloadStats

def test_strategy_protected():
    decision = determine_strategy("sys", None, Compatibility.PROTECTED, Mode.ADAPTIVE)
    assert decision.strategy == Strategy.PROTECTED

def test_strategy_quarantined():
    decision = determine_strategy("pandas", None, Compatibility.QUARANTINED, Mode.ADAPTIVE)
    assert decision.strategy == Strategy.EAGER

def test_strategy_insufficient_evidence():
    record = ModuleRecord(runs_requested=2) # Needs 3
    decision = determine_strategy("pandas", record, Compatibility.SAFE, Mode.ADAPTIVE)
    assert decision.strategy == Strategy.EAGER

def test_strategy_safe_mode():
    record = ModuleRecord(runs_requested=5)
    decision = determine_strategy("pandas", record, Compatibility.SAFE, Mode.SAFE)
    assert decision.strategy == Strategy.EAGER

def test_strategy_lazy():
    record = ModuleRecord(
        runs_requested=5,
        pre_readiness_runs=1, # 20%
        mean_cumulative_import_ns=30_000_000 # 30 ms (>= 25ms)
    )
    decision = determine_strategy("pandas", record, Compatibility.SAFE, Mode.ADAPTIVE)
    assert decision.strategy == Strategy.LAZY

def test_strategy_preload():
    record = ModuleRecord(
        runs_requested=5,
        pre_readiness_runs=5, # 100%
        mean_cumulative_import_ns=30_000_000, # 30 ms (>= 20ms)
        preload=PreloadStats(successes=2) # Has history of success
    )
    decision = determine_strategy("numpy", record, Compatibility.SAFE, Mode.ADAPTIVE)
    assert decision.strategy == Strategy.PRELOAD
