from typing import List, Dict, Tuple
from zenith.models import ImportMeasurement, ImportEvent, Phase
from zenith.storage.schema import ModuleRecord, CacheState

def merge_measurements_into_cache(
    measurements: List[ImportMeasurement], 
    cache_state: CacheState,
    update_history: bool = True
):
    """
    Merges exact profile measurements into the knowledge store.
    Measurements from `zenith profile` run.
    """
    for m in measurements:
        if not m.success:
            continue
            
        if m.module not in cache_state.modules:
            cache_state.modules[m.module] = ModuleRecord()
            
        record = cache_state.modules[m.module]
        
        # Exponential moving average or simple overwrite for mean cost
        # Since this is a profile measurement, we can just treat it as the current mean, 
        # or average it with existing if we wanted. For v2, let's just average it.
        if record.mean_self_import_ns is None:
            record.mean_self_import_ns = m.self_time_ns
        elif m.self_time_ns is not None:
            record.mean_self_import_ns = (record.mean_self_import_ns + m.self_time_ns) // 2
            
        if record.mean_cumulative_import_ns is None:
            record.mean_cumulative_import_ns = m.cumulative_time_ns
        elif m.cumulative_time_ns is not None:
            record.mean_cumulative_import_ns = (record.mean_cumulative_import_ns + m.cumulative_time_ns) // 2

def merge_runtime_events_into_cache(
    events: List[ImportEvent],
    cache_state: CacheState,
    run_id: str
):
    """
    Merges runtime observations (from SAFE/ADAPTIVE mode) into the knowledge store.
    """
    # First, aggregate events by module in this run
    run_modules: Dict[str, Phase] = {}
    
    for event in events:
        if event.module not in run_modules:
            run_modules[event.module] = event.phase
        else:
            # If we saw it POST_READINESS but earlier saw it PRE_READINESS,
            # we keep the earliest phase (PRE_READINESS).
            if event.phase == Phase.PRE_READINESS:
                run_modules[event.module] = Phase.PRE_READINESS
                
    # Update cache
    for module, phase in run_modules.items():
        if module not in cache_state.modules:
            cache_state.modules[module] = ModuleRecord()
            
        record = cache_state.modules[module]
        record.runs_requested += 1
        record.last_seen_run = run_id
        
        if phase == Phase.PRE_READINESS:
            record.pre_readiness_runs += 1
        else:
            record.post_readiness_runs += 1
