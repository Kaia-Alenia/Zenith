# ZENITH 2.0 — MASTER REDESIGN, ARCHITECTURE & IMPLEMENTATION SPECIFICATION

> **Status:** FINAL architectural specification  
> **Target:** Zenith 2.0  
> **Repository:** `Kaia-Alenia/alenia-zenith`  
> **Document role:** Source of truth for the implementation AI  
> **Language of implementation:** Python  
> **Minimum supported Python:** 3.10  
> **Primary runtime:** CPython  
> **Priority order:** Correctness → compatibility → observability → measurable performance → convenience

---

# 0. EXECUTIVE DECISION

Zenith 2.0 will **not** be a generic lazy-import library.

Zenith 2.0 will be:

> **An adaptive, observable and conservative startup optimization framework for Python applications.**

Its job is to understand import-related startup behavior, measure it, learn from repeated runs, decide whether any action is justified, execute only strategies considered sufficiently safe, and explain what it did.

The architecture is built around:

```text
OBSERVE
   ↓
MEASURE
   ↓
ANALYZE
   ↓
LEARN
   ↓
DECIDE
   ↓
EXECUTE
   ↓
VERIFY
   ↓
EXPLAIN
```

The old architecture:

```text
intercept imports → lazy proxy → remember → preload
```

is no longer the architecture of the project.

Lazy loading remains available, but only as **one optional execution backend**.

---

# 1. HOW TO USE THIS DOCUMENT

This file is the authoritative specification for the Zenith 2.0 implementation.

The implementation AI MUST:

1. read this complete document before modifying production code;
2. inspect the existing repository before deleting or reusing code;
3. implement the phases in the order defined here;
4. preserve working behavior only when it fits the new architecture;
5. add or update tests together with every architectural component;
6. measure performance instead of assuming it;
7. document any unavoidable deviation.

The implementation AI MUST NOT silently reinterpret requirements.

If implementation details differ from this document because Python itself makes a requirement impossible or unsafe, the implementation must:

1. choose the safest technically correct alternative;
2. document the deviation in code and changelog;
3. add a test proving the chosen behavior;
4. never fake the requested behavior.

---

# 2. NON-NEGOTIABLE RULES

These rules override all lower-level implementation suggestions.

## 2.1 Correctness comes first

Zenith is an optimization layer.

An application that works without Zenith should not require Zenith for correctness.

When Zenith lacks sufficient evidence to optimize a module, it must choose normal Python behavior.

```text
UNKNOWN → EAGER/NORMAL
UNSAFE → PROTECTED
FAILED OPTIMIZATION → QUARANTINE
```

## 2.2 No fabricated speed claims

Zenith must never say an application is faster unless a benchmark measured it.

Never calculate "expected saved milliseconds" and display them as actual savings.

Use explicit labels:

```text
MEASURED
ESTIMATED
HEURISTIC
HISTORICAL
```

## 2.3 No global lazy interception by default

`sys.meta_path` manipulation must not be installed in SAFE mode.

The lazy backend is opt-in through LAZY or ADAPTIVE mode and is subject to compatibility rules.

## 2.4 Observation and optimization are separate

The mechanism used to observe imports must not depend on lazy proxies.

The profiler must be usable while all imports retain normal Python semantics.

## 2.5 No silent exception swallowing

Any optimization failure must retain useful diagnostic information.

Exceptions caused by the application must preserve their original semantics and traceback wherever possible.

## 2.6 No telemetry

Zenith 2.0 sends no information over the network.

No analytics, remote reporting, cloud cache, package lookup, or automatic online compatibility database is part of v2.

## 2.7 No automatic source rewriting

Zenith may statically analyze source code.

Zenith 2.0 must not automatically edit application source files.

---

# 3. CURRENT ZENITH 1.x — AUDIT SUMMARY

The existing project already contains useful concepts and code.

Important current components include:

```text
zenith/__init__.py
zenith/cli.py
zenith/core/engine.py
zenith/core/constants.py
zenith/hooks/loader.py
zenith/speculation/predictor.py
zenith/transformer/ast_rewriter.py
tests/
benchmark.py
```

Current public concepts include:

```python
ignite()
warm()
exclude()
status()
analyze()
invalidate_cache()
```

These names are valuable and should be preserved when their semantics remain sensible.

## 3.1 What should be retained conceptually

Retain:

- simple one-call runtime initialization;
- explicit `warm()`;
- explicit exclusions;
- static source analysis;
- persistent history;
- CLI diagnostics;
- a lazy-import capability;
- zero mandatory runtime dependencies if practical;
- type information / `py.typed`;
- benchmark tooling;
- test coverage as a first-class concern.

## 3.2 What must change

The current implementation has architectural weaknesses that v2 must correct:

- the import hook is too central;
- lazy proxy behavior is coupled with observation;
- preload failures lose exception details;
- remembered modules are too simplistic to be called prediction;
- the cache lacks rich environment/profile information;
- the benchmark can confuse deferred work with actual total savings;
- compatibility classification is mostly a static exclusion set;
- strategy decisions are implicit rather than modeled;
- CLI `status` currently initializes Zenith, which is an undesirable side effect for a diagnostic command;
- there is no formal readiness boundary;
- there is no distinction between a measured result and a prediction.

---

# 4. PRODUCT DEFINITION

Zenith optimizes the **startup path** of Python applications.

A startup optimization can come from:

1. removing work from the readiness-critical path;
2. deferring optional import work;
3. starting safe future import work earlier;
4. identifying imports that developers should change manually;
5. learning repeated startup behavior;
6. avoiding strategies that previously failed.

Zenith does **not** make the underlying module initialization code magically execute faster.

This distinction must be reflected in the README, CLI, benchmarks, and API documentation.

---

# 5. WHAT ZENITH IS NOT

Zenith 2.0 is not:

- a package manager;
- a dependency resolver;
- a virtual environment manager;
- a Python compiler;
- a bundler;
- an application framework;
- an async framework;
- a generic CPU profiler;
- an APM product;
- an observability SaaS;
- a package installer;
- a code formatter;
- a source-to-source optimizer;
- a daemon;
- an ML system.

Do not expand scope into these areas.

---

# 6. TERMINOLOGY

The implementation must use these terms consistently.

## Import request

An attempt by application/runtime code to import a module.

## Module execution

Execution of a module's loader / initialization body.

## Import cost

Measured wall-clock time associated with loading/importing a module in a controlled profile.

## Self import time

Time attributable to the module excluding nested imports when the measurement source can provide it.

## Cumulative import time

Time including nested imports.

## Startup

The phase before the application declares or reaches its readiness boundary.

## Readiness boundary

The point after which the application considers its primary user-visible or service-ready startup complete.

## Early-process window

A time-based heuristic used only when no true readiness boundary exists.

It must never be mislabeled as guaranteed "critical startup".

## Observation

Collection of information without intentionally changing loading strategy.

## Strategy

A decision about how Zenith should treat a module.

## Backend

The mechanism that executes a strategy.

## Quarantine

A persistent safety state applied after an optimization strategy fails or behaves incompatibly.

---

# 7. CORE STRATEGIES

Every module decision resolves to one of four public strategies.

```text
EAGER
PRELOAD
LAZY
PROTECTED
```

Internally, `UNKNOWN` may exist before a decision is made, but it is not an executable optimization strategy.

## 7.1 EAGER

Use normal Python import semantics.

EAGER is the default when evidence is insufficient.

Reasons include:

- module is cheap;
- module is startup-critical;
- module compatibility is uncertain;
- no measurable benefit is expected;
- insufficient historical runs;
- optimization previously failed;
- user requested normal behavior.

## 7.2 PRELOAD

Start loading a module before its predicted point of need.

PRELOAD is speculative.

It must only be automatic when compatibility confidence is high.

It may run in a background worker only when the module satisfies the background-preload safety policy.

## 7.3 LAZY

Delay module execution until first meaningful use.

LAZY is optional and conservative.

It must use standard-library lazy mechanisms where possible rather than maintaining a custom module-proxy implementation without need.

## 7.4 PROTECTED

Never automatically alter this module's import behavior.

Protection may come from:

- user configuration;
- Zenith internals;
- Python runtime internals;
- compatibility rules;
- extension-module restrictions;
- previous failures;
- explicit project policy.

PROTECTED always wins over all automatic scoring.

---

# 8. OPERATING MODES

Zenith 2.0 exposes four modes.

```text
PROFILE
SAFE
LAZY
ADAPTIVE
```

## 8.1 PROFILE

Purpose:

> Measure and analyze with normal import semantics.

PROFILE must not install the optimization lazy finder.

It may launch the target application in an isolated subprocess for accurate CPython import timing.

## 8.2 SAFE

Purpose:

> Runtime learning and explicitly safe optimizations without global lazy interception.

SAFE is the default runtime mode.

Automatic behavior is intentionally conservative.

SAFE may:

- load history;
- record runtime observations;
- perform explicitly requested `warm()` operations;
- execute preloads only when allowed by policy;
- produce diagnostics.

SAFE must not make unknown modules lazy.

## 8.3 LAZY

Purpose:

> Enable lazy loading for explicitly eligible modules.

LAZY is opt-in.

It is not "make all imports lazy".

Compatibility and protection rules remain active.

## 8.4 ADAPTIVE

Purpose:

> Use accumulated evidence to select EAGER, PRELOAD, LAZY or PROTECTED.

ADAPTIVE is the advanced mode.

It still obeys minimum evidence requirements and safety policy.

Adaptive does not mean aggressive.

---

# 9. ARCHITECTURE

Required conceptual architecture:

```text
┌─────────────────────────────────────────────┐
│                 PUBLIC API                  │
│ ignite / profile / analyze / status / ...  │
└─────────────────────┬───────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌────────────────────┐
│ OBSERVATION      │    │ STATIC ANALYSIS    │
│ runtime events   │    │ source imports     │
│ profile subprocess│   │ dependency hints   │
└────────┬─────────┘    └─────────┬──────────┘
         │                        │
         └──────────┬─────────────┘
                    ▼
          ┌────────────────────┐
          │ PROFILE / HISTORY  │
          │ structured records │
          └─────────┬──────────┘
                    ▼
          ┌────────────────────┐
          │ COMPATIBILITY      │
          │ classification     │
          └─────────┬──────────┘
                    ▼
          ┌────────────────────┐
          │ STRATEGY ENGINE    │
          │ decision + reasons │
          └─────────┬──────────┘
                    ▼
          ┌────────────────────┐
          │ RUNTIME ENGINE     │
          └─────────┬──────────┘
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
     EAGER       PRELOAD        LAZY
     backend      backend       backend
                    │
                    ▼
          ┌────────────────────┐
          │ DIAGNOSTICS        │
          │ verify / explain   │
          └────────────────────┘
```

All major layers must communicate with typed data models.

Avoid passing unstructured dictionaries across the core architecture when a stable model exists.

---

# 10. FINAL DECISION: PROFILING ARCHITECTURE

Zenith will use a **hybrid observation architecture**.

No single profiling mechanism is sufficient for all needs.

The system will contain two observation paths.

## 10.1 Path A — isolated baseline import profiler

This is the authoritative profiler for CLI `zenith profile`.

For CPython, Zenith should prefer the interpreter's native import timing facility:

```bash
python -X importtime ...
```

For interpreters/versions where additional tracing features differ, Zenith must detect capability at runtime.

Important version behavior:

- `-X importtime` exists on supported Python versions;
- newer Python versions can provide additional already-loaded import tracing modes;
- Zenith must feature-detect rather than assume a single output capability.

The subprocess profiler:

- runs the target in a child process;
- captures import timing output separately from application stdout;
- parses import records;
- records self and cumulative time when available;
- records target exit code;
- never converts a failed application run into a successful profile;
- leaves the target's normal import strategy intact.

This path is the closest thing Zenith has to baseline ground truth.

## 10.2 Path B — lightweight runtime observer

Runtime `ignite()` needs historical knowledge without launching a second process.

The runtime observer collects low-overhead events such as:

- requested module;
- timestamp;
- whether already loaded;
- calling module when reliably available;
- process/run identifier;
- whether request happened before readiness.

It must delegate actual imports to Python unchanged in SAFE mode.

It must not pretend that its timings are equivalent to isolated `-X importtime` measurements.

Runtime event data is useful for frequency and ordering.

Baseline profiler data is useful for cost.

The Strategy Engine combines them.

---

# 11. WHY PROFILE MUST NOT USE THE LAZY BACKEND

The old design risks changing what is being measured.

If profiling activates lazy proxies:

```text
measured import time
≠
normal Python import time
```

That makes the profile unsuitable as a baseline.

Therefore:

> PROFILE observes normal import behavior. Optimization backends are disabled unless the user explicitly requests a comparative benchmark.

This rule is mandatory.

---

# 12. PROFILING TARGET EXECUTION

The CLI must support:

```bash
zenith profile app.py
zenith profile -m package.module
zenith profile -- python app.py --application-arg value
```

The exact parser may normalize these forms internally.

Requirements:

- preserve target arguments;
- preserve target exit status where possible;
- avoid importing the target inside the Zenith CLI process;
- execute the target in a child process;
- capture timing diagnostics;
- support JSON output;
- support human-readable output.

Suggested examples:

```bash
zenith profile app.py
zenith profile app.py --json
zenith profile -- python -m myapp
```

---

# 13. STARTUP / READINESS MODEL

A fixed "first five seconds" definition is not reliable enough to be the primary definition of startup.

Zenith 2.0 therefore uses a hierarchy.

## 13.1 Level 1 — explicit readiness marker

This is the preferred and authoritative readiness signal.

Public API:

```python
import zenith

zenith.mark_ready()
```

After this call:

```text
before mark_ready() → pre-readiness
after mark_ready()  → runtime
```

`mark_ready()` must be idempotent.

It must be extremely cheap.

Alternative name aliases must not proliferate. Use one public name: `mark_ready()`.

## 13.2 Level 2 — profile-controlled entrypoint boundary

When Zenith owns execution of a simple target through a wrapper and can unambiguously determine the completion of top-level initialization, it may record that boundary as an **entrypoint boundary**.

It must not automatically claim that this equals user-visible readiness.

## 13.3 Level 3 — heuristic early-process window

When no readiness marker exists, Zenith may classify events within a configurable time window.

Default:

```text
early_process_window = 2.0 seconds
```

This value is a heuristic.

Reports must call it:

```text
Early-process activity
```

not:

```text
Critical startup
```

Users may configure it:

```python
zenith.ignite(early_process_window=3.0)
```

or CLI equivalent.

## 13.4 Critical-startup claims

Zenith may call work "pre-readiness" or "critical-startup candidate" only when:

- an explicit readiness marker exists, or
- a supported integration provides a reliable readiness boundary.

Without that boundary, reports must remain conservative.

---

# 14. OBSERVATION DATA MODEL

Use dataclasses or similarly explicit typed models.

Conceptual model:

```python
@dataclass(frozen=True)
class ImportEvent:
    module: str
    monotonic_ns: int
    phase: Phase
    already_loaded: bool
    importer: str | None
    thread_id: int
```

Do not store `datetime.now()` for performance-critical ordering.

Use a monotonic clock for duration/order.

Wall-clock timestamps may be stored once at run metadata level.

---

# 15. PROFILE MEASUREMENT MODEL

Conceptual model:

```python
@dataclass
class ImportMeasurement:
    module: str
    self_time_ns: int | None
    cumulative_time_ns: int | None
    depth: int | None
    success: bool
    source: MeasurementSource
```

`None` is preferable to fabricated zero values when the source cannot provide a metric.

Measurement source examples:

```text
CPYTHON_IMPORTTIME
RUNTIME_OBSERVER
STATIC_ANALYSIS
BENCHMARK
```

---

# 16. RUN MODEL

Every observation session has a run record.

Conceptual fields:

```text
run_id
schema_version
zenith_version
python_implementation
python_version
python_cache_tag
platform
architecture
project_fingerprint
started_at
readiness_source
readiness_offset_ns
exit_code
mode
```

Never merge incompatible environments blindly.

---

# 17. PROJECT AND ENVIRONMENT FINGERPRINTING

Historical data can become invalid after dependency or interpreter changes.

Zenith must compute a stable local fingerprint.

Inputs should include when available:

- Python implementation;
- Python major/minor;
- cache tag / ABI-relevant identifier;
- platform;
- architecture;
- project root;
- `pyproject.toml` metadata/hash;
- common lock file hash when present.

Recognized lock files may include:

```text
uv.lock
poetry.lock
Pipfile.lock
requirements.txt
requirements-dev.txt
```

Do not hash entire virtual environments.

If dependency state changes, Zenith may retain old history for diagnostics but must not treat it as equal-confidence current evidence.

---

# 18. STATIC ANALYSIS

The existing AST analyzer remains useful.

Static analysis answers:

> What imports are syntactically present?

It does not answer:

> What imports actually execute?

Both data types must remain distinct.

Static analysis should collect:

- absolute imports;
- `from x import y`;
- import aliases;
- whether import is top-level or nested in a function/class/conditional where practical;
- source file and line number;
- `TYPE_CHECKING` context where practical.

Dynamic string imports are not required to be fully inferred.

Examples such as:

```python
importlib.import_module(name)
__import__(variable)
```

may be flagged as dynamic imports without guessing target names.

---

# 19. IMPORT DEPENDENCY RELATIONSHIPS

Zenith should record parent/child import relationships when the profiling source provides reliable nesting.

Example:

```text
pandas
 ├─ numpy
 └─ dateutil
```

Do not infer dependency edges solely from timing adjacency.

Each edge should include a source/confidence marker.

The dependency graph is useful for explanation and analysis, not for rewriting dependencies.

---

# 20. CACHE / KNOWLEDGE STORE

Zenith 2.0 replaces the simple module-name cache with a structured local knowledge store.

Default project-local directory:

```text
.zenith/
```

Recommended files:

```text
.zenith/
├── state.json
├── history.json
└── lock
```

The exact split may be simplified if one atomic state file is superior.

The directory should be documented for `.gitignore`.

No cache file should be written into the installed Zenith package directory.

---

# 21. CACHE SCHEMA

The schema must be versioned independently from the package version.

Initial schema:

```text
schema_version = 2
```

Conceptual JSON:

```json
{
  "schema_version": 2,
  "project": {
    "fingerprint": "..."
  },
  "environment": {
    "python_implementation": "CPython",
    "python_version": "3.x",
    "cache_tag": "...",
    "platform": "...",
    "architecture": "..."
  },
  "modules": {
    "numpy": {
      "runs_requested": 8,
      "pre_readiness_runs": 7,
      "post_readiness_runs": 1,
      "mean_self_import_ns": 42000000,
      "mean_cumulative_import_ns": 62000000,
      "last_seen_run": "...",
      "compatibility": "SAFE",
      "quarantine": null,
      "preload": {
        "attempts": 3,
        "successes": 3,
        "failures": 0
      },
      "lazy": {
        "attempts": 0,
        "successes": 0,
        "failures": 0
      }
    }
  }
}
```

The production schema may normalize data differently, but must preserve equivalent information.

---

# 22. CACHE SAFETY

Requirements:

- atomic replacement;
- UTF-8;
- validation before use;
- unknown fields tolerated when safe;
- unsupported schema handled gracefully;
- corrupted cache must never crash the target application;
- stale temporary files can be cleaned up;
- writes should be deterministic where practical.

## 22.1 Multi-process writes

Atomic replacement alone does not prevent lost updates.

Implement a simple cross-process lock strategy using standard-library primitives/files.

Requirements:

- bounded lock wait;
- stale lock recovery;
- no indefinite application shutdown hang;
- if lock cannot be acquired, skip persistence and record/log the reason.

Do not add a heavyweight runtime dependency only for locking.

---

# 23. HISTORY RETENTION

Unbounded history is not allowed.

Default policy:

```text
retain aggregate module statistics
retain last 50 run summaries
```

Raw event retention should be bounded.

CLI may expose:

```bash
zenith cache prune
```

but pruning can also occur automatically on write.

---

# 24. COMPATIBILITY CLASSIFICATION

Internal compatibility states:

```text
SAFE
CAUTION
UNSUPPORTED
PROTECTED
QUARANTINED
```

These are compatibility states, not loading strategies.

## PROTECTED

Policy says "never optimize automatically".

## QUARANTINED

A strategy previously failed or violated expectations.

Quarantine is stronger than normal scoring.

---

# 25. BUILT-IN PROTECTION RULES

At minimum, protect by default:

- `zenith` and its submodules;
- Python import machinery;
- built-in/frozen modules;
- modules where the loader cannot support the selected backend;
- modules explicitly excluded by the user.

Do **not** automatically protect the entire standard library forever merely because the v1 implementation did so.

Instead:

- EAGER should remain normal/default;
- LAZY/PRELOAD eligibility is evaluated by backend;
- core runtime/import machinery remains strictly protected.

A blanket standard-library exclusion may be kept initially as a conservative transitional policy for automatic optimization, but the compatibility system must be designed to become more precise.

---

# 26. C EXTENSION POLICY

Compiled extension modules require special caution.

Automatic LAZY or background PRELOAD must not be assumed safe for arbitrary extensions.

Policy:

```text
Unknown extension module → CAUTION → EAGER
```

It may become eligible only through:

- explicit user opt-in;
- a verified local compatibility record;
- future built-in rules supported by tests.

Zenith must never bypass Python extension safety checks.

---

# 27. BACKGROUND PRELOAD POLICY

Importing arbitrary packages in background threads can trigger thread-sensitive initialization and side effects.

Therefore automatic PRELOAD has a strict policy.

A module may be background-preloaded automatically only if all are true:

1. compatibility is SAFE;
2. it is not quarantined;
3. it has sufficient historical evidence;
4. it has at least two previously successful preload attempts in the same compatible environment **or** is explicitly allowlisted;
5. no previous preload failure exists in the current environment;
6. the user has not disabled background preload.

Unknown modules are not background-preloaded automatically.

`warm()` is explicit user intent and may attempt a preload, but failures must be surfaced diagnostically.

---

# 28. PRELOAD EXECUTION

The preload backend owns:

- worker pool;
- scheduling;
- deduplication;
- cancellation/shutdown;
- results;
- failure diagnostics.

Use a bounded `ThreadPoolExecutor`.

Default worker count:

```text
min(4, max(1, available_cpu_count))
```

The exact CPU count helper must handle `None`.

Worker count is configurable.

More workers do not imply better startup performance.

---

# 29. PRELOAD STATE MACHINE

Each preload candidate has states:

```text
NOT_SCHEDULED
SCHEDULED
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

Do not mark a module "preloaded" when merely submitted.

This corrects a weakness in the v1 engine, where scheduling and success are not cleanly distinguished.

---

# 30. FAILURE RECORDS

Store structured failures.

Conceptual model:

```python
@dataclass
class OptimizationFailure:
    module: str
    strategy: Strategy
    exception_type: str
    message: str
    monotonic_ns: int
    traceback_summary: str | None
```

Do not persist huge full tracebacks indefinitely.

Runtime status may retain recent detail.

Persistent history should store bounded summaries.

---

# 31. CRITICAL DECISION: LAZY BACKEND IMPLEMENTATION

Zenith 2.0 should prefer Python's standard:

```python
importlib.util.LazyLoader
```

where it is compatible.

Do not keep a custom `ZenithLazyModule` implementation as the default merely because it already exists.

The existing custom proxy must be audited.

If the standard `LazyLoader` can satisfy Zenith's needs, migrate to it.

A custom proxy may remain only if there is a specific, tested requirement the standard implementation cannot satisfy.

This reduces the amount of import machinery Zenith must own.

---

# 32. LAZY BACKEND LIMITATIONS

The backend must honor loader limitations.

Lazy behavior must not be applied when:

- the loader cannot support deferred execution;
- module replacement behavior makes lazy loading unsafe;
- compatibility classification forbids it;
- the module is protected;
- previous lazy execution failed.

Delayed exceptions are a known semantic cost of lazy loading.

Documentation must explain this.

---

# 33. LAZY FAILURE SEMANTICS

This is an important correction to the earlier draft.

Zenith must **not** promise that a partially executed lazy module can always "fall back to eager import".

Once module execution starts, side effects may already have happened.

Therefore:

```text
Failure before lazy installation
    → use normal EAGER behavior

Failure during deferred module execution
    → propagate the original exception
    → clean up only according to normal import semantics
    → quarantine that module/strategy for future runs
```

Never retry module execution automatically after a partial failure unless Python's semantics guarantee safety for that exact case.

---

# 34. IMPORT HOOK LIFECYCLE

When a lazy finder is installed:

- installation must be idempotent;
- Zenith must detect its own finder;
- repeated `ignite()` must not stack finders;
- finder removal must be supported for tests and controlled shutdown;
- finder must skip Zenith itself;
- finder recursion must be guarded.

Runtime state owns the hook.

Do not mutate global import state from unrelated modules.

---

# 35. `ignite()` SEMANTICS

Target API:

```python
zenith.ignite(
    mode="safe",
    *,
    workers=None,
    cache_path=None,
    exclude=None,
    include=None,
    verbose=False,
    early_process_window=2.0,
    background_preload=True,
)
```

Rules:

- keyword-only options after `mode`;
- validated mode enum;
- repeated identical initialization is idempotent;
- repeated conflicting initialization raises a clear `ZenithConfigurationError`;
- no ASCII banner by default;
- libraries should not print decorative output during import/runtime initialization;
- verbose diagnostics use logging, not unconditional `print()`.

The v1 banner behavior should be removed from default runtime behavior.

---

# 36. `mark_ready()`

Public API:

```python
zenith.mark_ready()
```

Behavior:

- idempotent;
- records readiness monotonic offset;
- updates runtime phase;
- no exception when called twice;
- if Zenith was not initialized, it may initialize only minimal readiness state or record a no-op according to final implementation, but it must not unexpectedly install optimization hooks.

Preferred behavior:

> `mark_ready()` without active Zenith is a cheap no-op.

---

# 37. `warm()`

Keep:

```python
zenith.warm("numpy", "requests")
```

Return a result object rather than only `None` if practical.

Conceptual:

```python
WarmResult(
    scheduled=("numpy", "requests"),
    skipped=(),
)
```

Do not block by default.

Optional future `wait=` can exist only if needed.

For v2, avoid unnecessary API complexity.

---

# 38. `exclude()` AND CONFIGURATION POLICY

Keep runtime exclusion support.

```python
zenith.exclude("torch")
```

Rules:

- exact root-package matching is the default;
- submodule patterns may be added through configuration if implemented safely;
- exclusion applies immediately to future strategy decisions;
- exclusions are represented as PROTECTED decisions.

Prefer explicit configuration over mutating a global module-level set used by unrelated runtime instances.

---

# 39. `status()`

`status()` must be side-effect free.

Calling:

```python
zenith.status()
```

must not:

- initialize worker pools;
- install import hooks;
- preload modules;
- create cache files merely to display status.

Return structured data.

CLI formats it.

---

# 40. `explain()`

Add:

```python
zenith.explain("pandas")
```

Conceptual result:

```text
Module: pandas
Strategy: LAZY
Compatibility: SAFE
Confidence: 0.87

Evidence:
- observed in 10 compatible runs
- pre-readiness request probability: 0.10
- mean import cost: 71.3 ms
- no lazy failures recorded

Decision:
- high cost
- low pre-readiness probability
- eligible lazy loader
```

Every reason must be derived from real data or explicit policy.

---

# 41. `analyze()`

Keep static analysis separate from dynamic profile.

```python
zenith.analyze("app.py")
```

It should not pretend static imports were actually executed.

Return structured analysis objects.

CLI may summarize them.

---

# 42. PUBLIC EXCEPTIONS

Define a small exception hierarchy.

```text
ZenithError
├── ZenithConfigurationError
├── ZenithProfileError
├── ZenithCacheError
└── ZenithBackendError
```

Normal application import exceptions should generally remain their original exception types rather than being unnecessarily wrapped.

---

# 43. STRATEGY ENGINE

Strategy selection receives:

```text
module profile
history
compatibility
mode
user policy
environment fingerprint
```

and emits:

```python
StrategyDecision(
    module=...,
    strategy=...,
    confidence=...,
    reasons=...,
    evidence_runs=...,
)
```

No backend execution happens inside the strategy engine.

It is a pure or near-pure decision component and should be heavily unit-tested.

---

# 44. MINIMUM EVIDENCE

Automatic optimization must not begin after a single run.

Defaults:

```text
minimum_compatible_runs = 3
preferred_confidence_runs = 5
```

With fewer than 3 compatible runs:

```text
automatic strategy → EAGER
```

unless:

- user explicitly requested lazy/preload;
- a built-in safe policy specifically permits it.

This favors safe learning.

---

# 45. STATISTICS

Use stable incremental statistics rather than storing every raw import timing forever.

At minimum compute:

- count;
- mean;
- min;
- max;
- recent exponentially weighted mean or bounded recent mean;
- pre-readiness frequency;
- post-readiness frequency;
- failure frequency.

Median/percentiles may be generated from bounded recent samples when enough data exists.

Do not claim statistically meaningful percentiles with tiny sample counts.

---

# 46. STRATEGY DEFAULT THRESHOLDS

Initial defaults are intentionally conservative and must be configurable internally.

## 46.1 LAZY candidate

Consider automatic LAZY only when:

```text
compatible_runs >= 3
compatibility == SAFE
mean_import_cost >= 25 ms
pre_readiness_probability <= 0.25
no lazy failures
not protected
```

This is only candidate eligibility.

Final decision may remain EAGER.

## 46.2 PRELOAD candidate

Consider automatic PRELOAD only when:

```text
compatible_runs >= 3
compatibility == SAFE
mean_import_cost >= 20 ms
pre_readiness_probability >= 0.80
not quarantined
background preload safety policy satisfied
```

## 46.3 EAGER

EAGER for everything not meeting a safer optimization condition.

These thresholds are v2 defaults, not universal truths.

Benchmark data may justify future changes.

---

# 47. CONFIDENCE

Confidence must not be a random opaque number.

Initial confidence should combine:

- sample sufficiency;
- consistency of phase usage;
- timing stability;
- compatibility confidence;
- absence of failures.

Keep the formula documented in code.

Prefer a simple inspectable formula over pseudo-AI complexity.

---

# 48. QUARANTINE

When an automatic strategy fails in a compatible environment:

```text
module + strategy → QUARANTINED
```

Default quarantine behavior:

- no automatic retry in the same run;
- future runs choose EAGER;
- diagnostics explain the quarantine.

User can clear quarantine:

```bash
zenith cache clear --module package
```

or equivalent.

Do not permanently blacklist a module across unrelated Python/dependency environments.

---

# 49. USER POLICY PRECEDENCE

Decision precedence:

```text
1. hard Zenith safety protection
2. explicit user PROTECTED/exclude
3. quarantine
4. explicit user include/strategy override where safe
5. compatibility classification
6. operating mode
7. historical strategy scoring
8. EAGER fallback
```

User overrides cannot disable non-negotiable Python safety protections.

---

# 50. LOGGING

Use Python `logging`.

Library default:

```text
no unsolicited stdout/stderr noise
```

CLI may print formatted output.

Runtime verbose mode raises Zenith logger verbosity.

Suggested logger:

```text
zenith
```

Do not embed ANSI color escapes inside core logic.

CLI rendering may use colors only when output is a TTY and must support no-color behavior.

---

# 51. CLI DESIGN

Target CLI:

```text
zenith profile
zenith analyze
zenith status
zenith explain
zenith benchmark
zenith cache
```

Suggested commands:

```bash
zenith profile app.py
zenith profile -- python -m myapp

zenith analyze app.py

zenith status
zenith status --json

zenith explain pandas
zenith explain pandas --json

zenith benchmark app.py
zenith benchmark app.py --mode safe
zenith benchmark app.py --mode adaptive

zenith cache inspect
zenith cache clear
zenith cache clear --module pandas
zenith cache prune
```

Do not create dozens of shallow commands.

---

# 52. CLI EXIT CODES

Use predictable exit behavior.

Suggested:

```text
0  success
1  Zenith command/profile failure
2  invalid CLI usage/configuration
target exit code preserved where profile/run semantics require it
```

When preserving arbitrary target exit codes conflicts with CLI error semantics, report both clearly and document the chosen mapping.

---

# 53. JSON OUTPUT

Machine-readable output is required for major diagnostic commands.

Use:

```bash
--json
```

JSON output must:

- contain no decorative text;
- be stable enough for tooling;
- include a schema/version field when appropriate;
- separate measured and estimated values.

---

# 54. BENCHMARK PHILOSOPHY

Benchmarking must answer:

> Did Zenith make the useful startup milestone faster without unacceptable regressions?

It must not answer only:

> Did the `import` statement return faster because work was deferred?

---

# 55. BENCHMARK MODES

Benchmarks should support:

```text
BASELINE
SAFE
LAZY
ADAPTIVE
```

Every benchmark comparison must run in isolated subprocesses.

Do not benchmark baseline and Zenith in the same long-lived Python interpreter.

---

# 56. BENCHMARK WARMUP

Separate:

```text
cold Zenith state
warm learned Zenith state
```

Do not silently compare a warm Zenith cache against an unexplained baseline.

Reports must state cache condition.

---

# 57. BENCHMARK METRICS

At minimum:

```text
process startup wall time
readiness time when mark_ready() is available
target exit time
Zenith overhead
import self/cumulative timing where available
preload work completed before readiness
deferred work executed after readiness
```

Optional:

```text
peak RSS / memory
```

Memory metrics should only be shown when measured reliably on the platform.

---

# 58. BENCHMARK STATISTICS

Defaults:

```text
warmups = 2
measured_runs = 10
```

Report:

- median;
- mean;
- min/max;
- standard deviation when sample count permits.

Prefer median as headline latency metric.

A single run must not produce a percentage performance claim in README.

---

# 59. PERFORMANCE REGRESSION POLICY

Zenith itself must have overhead budgets.

Initial engineering targets:

```text
SAFE initialization median overhead:
  target <= 5 ms on a lightweight reference app

runtime observer overhead:
  target low enough to avoid material startup regression

status/explain when uninitialized:
  must not initialize optimization runtime
```

These are engineering targets, not guaranteed public promises.

CI benchmarks may use wider environment-specific thresholds to avoid flaky failures.

---

# 60. TEST ARCHITECTURE

Tests must include both unit and subprocess integration tests.

Import behavior should not be tested only in the pytest interpreter because global import state leaks between tests.

Use subprocess tests for:

- hook installation;
- circular imports;
- lazy execution;
- failed imports;
- `sys.modules` semantics;
- namespace packages;
- package/submodule behavior;
- repeated interpreter starts;
- cache learning;
- CLI profile;
- benchmark isolation.

---

# 61. REQUIRED IMPORT TEST MATRIX

At minimum:

```text
plain Python module
package __init__
submodule
from package import name
relative import
namespace package
circular import
module raising ImportError
module raising arbitrary exception during init
module imported twice
module already in sys.modules
module using importlib.import_module
module with import-time side effects
built-in module
frozen module
pure-Python stdlib module
third-party pure Python fixture
compiled-extension fixture when CI environment provides one
concurrent import
```

---

# 62. LAZY TEST MATRIX

Verify:

- body is not executed before intended trigger;
- first attribute access executes once;
- concurrent first access executes once;
- exception preserves semantics;
- failed module is quarantined for future automatic decisions;
- parent/submodule relationships remain correct;
- protected modules bypass lazy backend;
- finder does not recursively intercept itself;
- finder installation is idempotent;
- uninstall in tests restores `sys.meta_path`.

---

# 63. PRELOAD TEST MATRIX

Verify:

- submission is distinct from success;
- duplicates do not schedule twice;
- success recorded only after completion;
- failure retains exception metadata;
- shutdown does not hang indefinitely;
- explicit warm behavior is observable;
- unknown automatic modules are not background-preloaded;
- quarantine blocks automatic reattempt;
- race with foreground import does not corrupt module state.

---

# 64. CACHE TEST MATRIX

Verify:

- first creation;
- atomic update;
- corruption recovery;
- unsupported schema;
- lock contention;
- stale lock recovery;
- environment fingerprint mismatch;
- project fingerprint change;
- bounded history;
- per-module clearing;
- quarantine clearing;
- no crash when directory is read-only.

When cache persistence fails, application execution should normally continue.

---

# 65. PROFILE TEST MATRIX

Verify:

- target stdout remains distinguishable from profiler diagnostics;
- import timing is parsed correctly;
- failed target remains failed;
- arguments pass through;
- module execution mode works;
- spaces/unicode in paths;
- Python 3.10+ capability detection;
- output parser handles CPython-version differences;
- JSON report schema.

---

# 66. PROPERTY / INVARIANT TESTS

Important invariants:

```text
PROTECTED is never auto-optimized.
SAFE mode never installs lazy interception.
status() has no optimization side effects.
failed lazy execution is not blindly retried.
unknown module defaults to EAGER.
cache corruption never prevents target startup.
one successful run is insufficient for adaptive auto-optimization.
```

These should be explicit tests.

---

# 67. CI MATRIX

Recommended CI:

```text
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
latest supported stable Python
```

When Python 3.15 becomes stable and supported, add it after tests pass.

Operating systems:

```text
Linux
Windows
macOS
```

At minimum, full matrix may be reduced for cost, but import-system integration tests should run across all three major OS families periodically/release-time.

---

# 68. TYPE CHECKING

Retain `py.typed`.

Use modern typing compatible with Python 3.10.

Avoid syntax that accidentally raises minimum Python above 3.10 unless `from __future__ import annotations` and compatible constructs are used correctly.

Mypy strict mode is desirable.

Typing errors in existing v1 code such as informal `X or None` annotations must be corrected.

---

# 69. FORMATTING / LINTING

Keep tooling focused.

Recommended dev tools:

```text
pytest
mypy
ruff
```

Do not add a large framework of development dependencies.

Ruff may handle linting/formatting if adopted.

---

# 70. PACKAGE METADATA

Update `pyproject.toml` for 2.0.

Requirements:

- accurate Python classifiers;
- accurate development status;
- clear project description;
- CLI entry point;
- `py.typed` included;
- license metadata valid;
- optional dev dependencies;
- no mandatory dependencies unless justified.

Do not claim Python versions that CI does not test.

---

# 71. VERSIONING

Target:

```text
2.0.0
```

Use semantic versioning principles.

Cache schema version is independent of package version.

Do not manually duplicate the package version in many source files.

Prefer a single version source through package metadata or one internal constant.

---

# 72. BACKWARD COMPATIBILITY

Preserve where sensible:

```python
ignite()
warm()
exclude()
status()
analyze()
invalidate_cache()
```

But semantics may become safer.

Breaking changes permitted in 2.0:

- banner removed by default;
- `ignite()` configuration redesigned;
- richer status return type;
- cache format changed;
- lazy behavior no longer implicit/global;
- CLI command behavior improved.

Document migration clearly.

---

# 73. OLD CACHE MIGRATION

Zenith 1.x `.zenith_cache.json` contains insufficient information for adaptive decisions.

Migration policy:

- detect legacy cache;
- optionally import module names as low-confidence historical hints;
- never treat legacy names as sufficient evidence for automatic optimization;
- write new v2 state separately;
- do not destroy legacy cache until v2 state writes successfully.

A simpler valid choice is to ignore legacy data after documenting the behavior.

Preferred choice:

> Import as low-confidence hints, never as optimization evidence.

---

# 74. README REWRITE REQUIREMENTS

The public README must eventually describe reality, not aspiration.

README order:

1. what Zenith is;
2. when it helps;
3. when it may not help;
4. install;
5. safe quick start;
6. profile workflow;
7. modes;
8. benchmark methodology;
9. compatibility/safety;
10. API/CLI;
11. development.

Remove marketing phrases that imply guaranteed acceleration.

Do not use "magic".

---

# 75. DOCUMENTATION EXAMPLE — SAFE START

Recommended quick start:

```python
import zenith

zenith.ignite()

# application imports / startup work

zenith.mark_ready()
```

Explain that `mark_ready()` improves analysis but is optional.

---

# 76. DOCUMENTATION EXAMPLE — PROFILE FIRST

Recommended developer workflow:

```bash
zenith profile app.py
```

Then:

```bash
zenith analyze app.py
zenith explain some_module
```

The product should encourage measurement before aggressive mode changes.

---

# 77. SECURITY

Zenith processes source paths and launches profile subprocesses.

Security rules:

- never execute arbitrary shell strings with `shell=True`;
- pass subprocess argument arrays;
- do not download compatibility data;
- cache filenames must not allow traversal;
- sanitize CLI-provided module identifiers;
- do not deserialize pickle for persistent state;
- JSON only for cache/report data unless a similarly safe stdlib format is justified.

---

# 78. PRIVACY

All collected history is local.

Document exactly what is stored.

Do not store:

- source code contents in history;
- environment variables wholesale;
- command-line secrets;
- full arbitrary application output.

Target command metadata should be minimized.

---

# 79. FORK / MULTIPROCESS BEHAVIOR

Worker pools and import hooks interact poorly with process forking if unmanaged.

Policy:

- do not start background workers earlier than necessary;
- detect PID changes in runtime state;
- child process should not blindly reuse parent's executor state;
- cache writes use process-safe locking;
- document limitations for multiprocessing.

Integration tests should include basic multiprocessing where supported.

---

# 80. THREAD SAFETY

Core mutable runtime state must have explicit ownership and locking.

Avoid one global lock around all runtime operations.

Required separately protected areas:

- initialization;
- cache persistence;
- preload state;
- strategy/history mutation.

Do not hold Zenith locks while executing arbitrary third-party module code if avoidable.

---

# 81. SHUTDOWN

`atexit` work must be bounded.

At shutdown:

1. capture final aggregate state;
2. stop accepting new preload tasks;
3. attempt bounded persistence;
4. do not wait forever for background imports.

Default shutdown should favor application termination over perfect cache persistence.

---

# 82. RUNTIME STATE

Replace scattered global variables with a runtime state object.

Conceptual:

```python
class ZenithRuntime:
    config
    observer
    knowledge_store
    compatibility
    strategy_engine
    preload_backend
    lazy_backend
    readiness
```

A module-level singleton may expose the simple API, but state ownership must be explicit.

This greatly improves tests and lifecycle handling.

---

# 83. DEPENDENCY INJECTION FOR TESTABILITY

Core components should accept interfaces/protocols where useful:

```text
clock
storage
profiler runner
compatibility rules
backend
```

Do not over-engineer a DI framework.

Simple constructor injection is enough.

A fake monotonic clock is particularly useful for deterministic tests.

---

# 84. DIRECTORY STRUCTURE — TARGET

Recommended:

```text
zenith/
├── __init__.py
├── api.py
├── config.py
├── models.py
├── runtime.py
│
├── observation/
│   ├── __init__.py
│   ├── runtime.py
│   └── importtime.py
│
├── analysis/
│   ├── __init__.py
│   ├── static.py
│   └── profiles.py
│
├── strategy/
│   ├── __init__.py
│   ├── engine.py
│   └── scoring.py
│
├── compatibility/
│   ├── __init__.py
│   └── rules.py
│
├── backends/
│   ├── __init__.py
│   ├── preload.py
│   └── lazy.py
│
├── storage/
│   ├── __init__.py
│   ├── schema.py
│   └── cache.py
│
├── diagnostics/
│   ├── __init__.py
│   ├── status.py
│   └── explain.py
│
└── cli/
    ├── __init__.py
    └── main.py
```

This is a responsibility map, not a command to create empty files.

Do not create a directory/module until it has a real responsibility.

---

# 85. DATA CLASSES / ENUMS

Recommended central models:

```text
Mode
Strategy
Compatibility
Phase
MeasurementSource
PreloadState
ImportEvent
ImportMeasurement
ModuleHistory
RunSummary
StrategyDecision
OptimizationFailure
ZenithStatus
ZenithConfig
```

Enums should serialize to stable lowercase or uppercase strings consistently.

---

# 86. NO FALSE "AI"

Zenith's predictor is statistical/rule-based in 2.0.

Do not call it:

```text
AI-powered
machine learning
neural prediction
```

unless the project actually adds such technology in a future major feature.

"Adaptive" and "learns from run history" are accurate descriptions.

---

# 87. PERFORMANCE MEASUREMENT SOURCES

The implementation must distinguish:

## Native import timing

Controlled CPython import timing from isolated process.

## Runtime event timing

Low-overhead event chronology.

## Application readiness timing

Explicit marker when provided.

## End-to-end benchmark timing

External process wall-clock measurement.

Do not merge these into one ambiguous `time_ms`.

---

# 88. REPORTING EXAMPLE

Human output should resemble:

```text
Zenith Startup Profile
────────────────────────────────────────

Target: app.py
Python: CPython 3.x

Readiness:
  explicit marker: yes
  reached at: 418.2 ms

Measured imports before readiness:
  pandas     self 71.4 ms   cumulative 95.2 ms
  numpy      self 39.8 ms   cumulative 42.1 ms
  requests   self  7.7 ms   cumulative 19.3 ms

Historical evidence:
  compatible runs: 6

Recommendations:
  numpy      PRELOAD   confidence 0.84
  pandas     EAGER     confidence 0.91

Notes:
  pandas remains EAGER because it is requested before readiness
  in 6/6 compatible runs.
```

If no readiness marker exists:

```text
Readiness:
  explicit marker: no
  using: 2.0 s early-process heuristic
```

Do not call that result exact critical startup.

---

# 89. `status()` EXAMPLE

```text
Zenith 2.0
Mode: adaptive
Initialized: yes
Readiness marked: yes

History:
  compatible runs: 8
  tracked modules: 37

Current strategies:
  EAGER: 25
  PRELOAD: 4
  LAZY: 2
  PROTECTED: 6

Backend:
  preload workers: 2
  lazy finder: installed

Failures:
  recent: 0
  quarantined strategies: 1
```

---

# 90. EXPLAINABILITY REQUIREMENTS

Every automatic non-EAGER decision must provide at least:

- strategy;
- compatibility state;
- evidence run count;
- key probability/frequency;
- import cost evidence;
- safety policy result;
- reasons.

If a decision came from explicit user configuration, say so.

Example:

```text
Strategy: PROTECTED
Reason: explicitly excluded by configuration
```

---

# 91. DIAGNOSTIC SELF-CHECK

Add:

```bash
zenith doctor
```

only if implementation remains focused.

It may validate:

- cache writable;
- Python capability;
- lazy backend availability;
- duplicate finder state;
- configuration validity.

This command is optional for 2.0 final release.

It must not block completion of core architecture.

---

# 92. FEATURES EXPLICITLY DEFERRED

Not part of 2.0:

- ML models;
- remote compatibility service;
- GUI;
- web dashboard;
- IDE plugin;
- source rewriting;
- automatic moving of imports inside functions;
- binary patching;
- package installation;
- cloud telemetry;
- distributed prediction;
- cross-machine cache sync;
- daemonized warm cache;
- OS page-cache manipulation;
- persistent worker process;
- preload through subprocess injection.

---

# 93. IMPLEMENTATION PHASE 0 — BASELINE FREEZE

Before redesign:

1. run current tests;
2. record failures;
3. run current benchmark only as historical reference;
4. inspect current public API;
5. create a v1 behavior inventory.

Do not treat current benchmark claims as acceptance criteria.

Deliverable:

```text
docs/zenith-v1-audit.md
```

or equivalent internal notes.

---

# 94. PHASE 1 — CORE MODELS AND CONFIGURATION

Implement:

- enums;
- config validation;
- runtime state;
- exception hierarchy;
- status model;
- no optimization yet.

Acceptance:

- tests pass;
- `ignite(mode="safe")` initializes state;
- conflicting repeated initialization handled;
- no import hook installed in SAFE.

---

# 95. PHASE 2 — STORAGE V2

Implement:

- schema;
- environment/project fingerprint;
- atomic storage;
- locking;
- corruption recovery;
- bounded history;
- legacy cache migration/hints.

Acceptance:

- cache failure cannot break normal app startup;
- schema tests complete.

---

# 96. PHASE 3 — STATIC ANALYSIS

Refactor existing AST functionality.

Acceptance:

- static imports represented as structured results;
- nested/top-level context where practical;
- no source modification;
- dynamic unknown imports identified rather than guessed.

---

# 97. PHASE 4 — ISOLATED PROFILE

Implement `-X importtime` subprocess profiling.

Acceptance:

- Python 3.10+ support;
- parser version capability tests;
- target args preserved;
- JSON report;
- failed target represented correctly;
- no lazy backend involved.

This phase is one of the most important.

---

# 98. PHASE 5 — RUNTIME OBSERVER AND READINESS

Implement:

- event observer;
- `mark_ready()`;
- phase classification;
- run aggregation.

Acceptance:

- SAFE observer does not change import result semantics;
- explicit readiness works;
- heuristic clearly labeled.

---

# 99. PHASE 6 — ANALYSIS / HISTORY

Combine:

- profile cost;
- runtime frequency;
- readiness history;
- environment compatibility.

Acceptance:

- module summaries deterministic;
- incompatible environment evidence separated;
- statistics tested.

---

# 100. PHASE 7 — COMPATIBILITY

Implement rule engine.

Acceptance:

- hard protected modules;
- loader inspection;
- extension caution;
- user excludes;
- quarantine.

No automatic lazy/preload yet.

---

# 101. PHASE 8 — STRATEGY ENGINE

Implement decisions and confidence.

Acceptance:

- pure unit tests for threshold boundaries;
- unknown → EAGER;
- protected → PROTECTED;
- reasons always present for optimization decisions;
- minimum evidence enforced.

---

# 102. PHASE 9 — PRELOAD BACKEND

Refactor v1 engine.

Acceptance:

- correct state machine;
- structured failures;
- policy gating;
- no scheduling counted as success;
- shutdown bounded;
- race tests.

---

# 103. PHASE 10 — LAZY BACKEND

Audit custom hook.

Prefer standard `importlib.util.LazyLoader`.

Acceptance:

- backend isolated;
- eligibility checks;
- idempotent finder lifecycle;
- circular/import failure tests;
- partial execution not blindly retried;
- quarantine.

---

# 104. PHASE 11 — ADAPTIVE MODE

Connect:

```text
history → compatibility → strategy → backend
```

Acceptance:

- conservative first runs;
- automatic strategies appear only after evidence;
- decisions explainable;
- failures downgrade future behavior.

---

# 105. PHASE 12 — CLI / REPORTING

Implement final CLI.

Acceptance:

- human and JSON output;
- status side-effect free;
- profile/analyze/explain/cache commands;
- clean error messages;
- no core ANSI coupling.

---

# 106. PHASE 13 — BENCHMARK HARNESS

Implement robust isolated benchmark.

Acceptance:

- warmup;
- multiple runs;
- baseline/mode comparison;
- median headline;
- cache state declared;
- readiness-aware when marker exists.

---

# 107. PHASE 14 — DOCUMENTATION / MIGRATION

Rewrite:

```text
README.md
README-es.md
CHANGELOG.md
migration guide
```

Documentation must match final implementation.

No aspirational features listed as existing.

---

# 108. PHASE 15 — RELEASE GATE

Before `2.0.0`:

- full test matrix;
- mypy;
- lint;
- package build/install test;
- CLI smoke test;
- three-OS validation;
- benchmark report;
- cache migration test;
- README commands verified.

---

# 109. DEFINITION OF DONE

Zenith 2.0 is complete only when all are true.

## Architecture

- observation separated from optimization;
- strategy separated from backend;
- explicit runtime state;
- lazy optional.

## Profiling

- isolated normal-semantics import profile works;
- costs represented accurately within source capability;
- readiness labeling is honest.

## Learning

- v2 store persists structured evidence;
- fingerprinting prevents blind reuse;
- minimum-run policy works.

## Safety

- unknown defaults EAGER;
- protected and quarantine work;
- C extensions treated conservatively;
- partial lazy failure is not blindly retried.

## Observability

- status;
- explain;
- structured failures;
- JSON output.

## Performance

- isolated benchmark harness;
- no unsupported claims;
- Zenith overhead measured.

## Quality

- test matrix;
- supported Python versions in CI;
- typed package;
- docs synchronized.

---

# 110. RELEASE PERFORMANCE CLAIM POLICY

README performance examples may be included only after final benchmark data exists.

Every published benchmark must state:

- hardware/OS;
- Python version;
- target workload;
- number of runs;
- cold/warm state;
- mode;
- metric;
- median;
- comparison baseline.

Do not publish:

```text
"Zenith makes Python X% faster"
```

Acceptable:

```text
"On benchmark X, adaptive mode reduced median time-to-readiness
from A ms to B ms across N measured runs."
```

---

# 111. DESIGN DECISIONS — FINAL TABLE

| Topic | Final decision |
|---|---|
| Product identity | Adaptive startup optimization framework |
| Default mode | SAFE |
| Default unknown strategy | EAGER |
| Global lazy hook in SAFE | No |
| Profile mechanism | Isolated native CPython import timing + parser |
| Runtime observation | Lightweight, semantics-preserving observer |
| Readiness | Explicit `mark_ready()` preferred |
| No readiness marker | 2s early-process heuristic, clearly labeled |
| Lazy implementation | Prefer stdlib `importlib.util.LazyLoader` |
| Custom lazy proxy | Keep only if proven necessary |
| Lazy partial failure | Propagate, quarantine; no blind eager retry |
| Automatic preload | Conservative, evidence + safety gated |
| Unknown C extension | CAUTION / EAGER |
| Minimum auto evidence | 3 compatible runs |
| Preferred evidence | 5+ runs |
| Initial lazy cost threshold | 25 ms |
| Initial lazy startup probability | <= 25% |
| Initial preload cost threshold | 20 ms |
| Initial preload startup probability | >= 80% |
| Cache | Versioned JSON local store |
| Cache writes | Atomic + bounded cross-process lock |
| Legacy cache | Low-confidence hint only |
| Telemetry | None |
| Runtime dependencies | Zero preferred |
| Logging | stdlib logging |
| Default banner | Removed |
| CLI status side effects | None |
| Benchmark headline | Median isolated process latency/readiness |
| AI/ML claims | None |
| Source rewriting | Out of scope |
| Supported Python baseline | 3.10+ |
| Primary interpreter | CPython |

---

# 112. IMPLEMENTATION AI — PROHIBITED SHORTCUTS

The implementation AI must not:

- rename architectural concepts merely for style;
- use a custom import proxy before testing stdlib LazyLoader;
- turn all imports lazy;
- preload every historical module;
- use one run as prediction;
- swallow `Exception` without recording detail;
- mark submitted preload tasks as successful;
- call `ignite()` from `status`;
- make cache corruption fatal;
- compare benchmarks inside the same interpreter;
- claim a time window is true application readiness;
- add network calls;
- add ML;
- rewrite user source;
- keep dead v1 architecture just to reduce diff size;
- delete useful tests to make a redesign pass.

---

# 113. IMPLEMENTATION AI — REQUIRED WORK STYLE

For each phase:

1. inspect relevant current code;
2. identify reusable behavior;
3. write/adjust tests;
4. implement smallest coherent architecture;
5. run tests;
6. run typing/lint where configured;
7. update implementation notes;
8. continue only after phase invariants hold.

Large destructive rewrite commits should be avoided when incremental migration can preserve verifiability.

---

# 114. EXPECTED USER EXPERIENCE

A new user should be able to do:

```bash
pip install alenia-zenith
zenith profile app.py
```

and immediately receive useful information without modifying their source.

For runtime learning:

```python
import zenith

zenith.ignite()

# application initialization

zenith.mark_ready()
```

After several compatible runs:

```python
zenith.explain("some_heavy_module")
```

may show why Zenith recommends or applies a strategy.

Advanced users may opt into:

```python
zenith.ignite(mode="adaptive")
```

without losing the ability to inspect every decision.

---

# 115. CORE PHILOSOPHY

Zenith should be boring when it lacks evidence.

That is a feature.

A startup optimizer that occasionally breaks imports is worse than no optimizer.

The desired progression is:

```text
first run:
    observe

next runs:
    learn

enough evidence:
    recommend

safe evidence:
    optimize

unexpected result:
    stop / quarantine / explain
```

Not:

```text
install
→ intercept everything
→ hope it is faster
```

---

# 116. FINAL ARCHITECTURAL VISION

Zenith 1.x:

```text
IMPORT HOOK
   ↓
LAZY MODULE
   ↓
CACHE NAME
   ↓
PRELOAD NEXT TIME
```

Zenith 2.0:

```text
                 NORMAL PYTHON BEHAVIOR
                          │
                          ▼
                    OBSERVATION
                    /         \
                   /           \
          STATIC ANALYSIS    PROFILE
                   \           /
                    \         /
                     KNOWLEDGE
                         │
                         ▼
                  COMPATIBILITY
                         │
                         ▼
                  STRATEGY ENGINE
                         │
               ┌─────────┼─────────┐
               ▼         ▼         ▼
             EAGER    PRELOAD     LAZY
               │         │         │
               └─────────┼─────────┘
                         ▼
                      VERIFY
                         │
                         ▼
                 HISTORY / EXPLAIN
```

Zenith 2.0 is successful when it can answer all of these questions:

```text
What happened during startup?
How expensive was it?
Which evidence is measured?
Which evidence is historical?
Which imports occur before readiness?
What strategy is being used?
Why was that strategy selected?
Is the module compatible?
Did the optimization actually succeed?
Did startup measurably improve?
What will Zenith do if the optimization fails?
```

If Zenith cannot answer those questions, the architecture is incomplete.

---

# 117. FINAL DIRECTIVE

Build Zenith 2.0 as a **measurement-first, safety-first, evidence-driven optimizer**.

Do not optimize for cleverness.

Optimize for:

```text
correctness
predictability
compatibility
explainability
measurable value
```

The strongest differentiator of Zenith should not be that it can manipulate Python imports.

Python already exposes import machinery.

The differentiator should be that Zenith can:

> **observe real startup behavior, accumulate trustworthy evidence, choose a conservative strategy, execute it through isolated backends, verify the result, and explain the decision.**

That is the final design.

---

# END — ZENITH 2.0 MASTER SPECIFICATION
