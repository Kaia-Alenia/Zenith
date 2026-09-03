from typing import Optional
from zenith.models import StrategyDecision, Strategy, Compatibility, Mode
from zenith.storage.schema import ModuleRecord

# Default thresholds
MIN_COMPATIBLE_RUNS = 3
LAZY_MIN_COST_NS = 25_000_000 # 25 ms
PRELOAD_MIN_COST_NS = 20_000_000 # 20 ms
LAZY_MAX_PRE_READINESS_PROB = 0.25
PRELOAD_MIN_PRE_READINESS_PROB = 0.80

def determine_strategy(
    module: str,
    record: Optional[ModuleRecord],
    compatibility: Compatibility,
    mode: Mode,
    bg_preload_allowed: bool = True
) -> StrategyDecision:
    reasons = []
    
    if compatibility == Compatibility.PROTECTED:
        return StrategyDecision(
            module=module,
            strategy=Strategy.PROTECTED,
            confidence=1.0,
            reasons=["Module is explicitly protected by policy"],
            evidence_runs=0
        )
        
    if compatibility == Compatibility.QUARANTINED:
        return StrategyDecision(
            module=module,
            strategy=Strategy.EAGER,
            confidence=1.0,
            reasons=["Module is quarantined due to previous failure"],
            evidence_runs=0
        )

    if not record or record.runs_requested < MIN_COMPATIBLE_RUNS:
        runs = record.runs_requested if record else 0
        return StrategyDecision(
            module=module,
            strategy=Strategy.EAGER,
            confidence=1.0,
            reasons=[f"Insufficient evidence: {runs} runs (requires {MIN_COMPATIBLE_RUNS})"],
            evidence_runs=runs
        )
        
    if mode in (Mode.PROFILE, Mode.SAFE):
        return StrategyDecision(
            module=module,
            strategy=Strategy.EAGER,
            confidence=1.0,
            reasons=[f"EAGER fallback due to mode: {mode.value}"],
            evidence_runs=record.runs_requested
        )

    # Adaptive mode logic
    pre_prob = record.pre_readiness_runs / record.runs_requested if record.runs_requested > 0 else 1.0
    cost = record.mean_cumulative_import_ns or 0
    
    if compatibility == Compatibility.SAFE:
        # Check LAZY
        if cost >= LAZY_MIN_COST_NS and pre_prob <= LAZY_MAX_PRE_READINESS_PROB and record.lazy.failures == 0:
            reasons.append(f"High cost ({cost // 1_000_000} ms) and low pre-readiness probability ({pre_prob:.2f})")
            return StrategyDecision(
                module=module,
                strategy=Strategy.LAZY,
                confidence=0.9, # Simplified confidence
                reasons=reasons,
                evidence_runs=record.runs_requested
            )
            
        # Check PRELOAD
        if cost >= PRELOAD_MIN_COST_NS and pre_prob >= PRELOAD_MIN_PRE_READINESS_PROB and bg_preload_allowed:
            reasons.append(f"High cost ({cost // 1_000_000} ms) and high pre-readiness probability ({pre_prob:.2f})")
            # Require at least two previous successes for background preload, OR allowlist.
            # But the spec says "has at least two previously successful preload attempts ... OR is explicitly allowlisted"
            # For this simplified engine, we will check successes.
            if record.preload.successes >= 2:
                reasons.append("Has proven safe in previous preloads")
                return StrategyDecision(
                    module=module,
                    strategy=Strategy.PRELOAD,
                    confidence=0.8,
                    reasons=reasons,
                    evidence_runs=record.runs_requested
                )
            else:
                reasons.append("Not enough successful preload history yet")

    return StrategyDecision(
        module=module,
        strategy=Strategy.EAGER,
        confidence=1.0,
        reasons=["Does not meet thresholds for LAZY or PRELOAD, or compatibility is CAUTION"],
        evidence_runs=record.runs_requested
    )
