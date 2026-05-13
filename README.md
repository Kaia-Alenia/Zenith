# Zenith

[![Python Version](https://img.shields.io/badge/python-3.14%20%7C%203.15-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Alenia%20Studios%201.0-orange.svg)](https://github.com/Kaia-Alenia/Zenith/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-red.svg)](https://github.com/Kaia-Alenia/Zenith)

Zero-latency boot infrastructure for Python applications.

Zenith is an advanced speculative execution pre-loader designed to eliminate Python's startup import latency. By leveraging Python 3.14's native free-threading model (PEP 703) and fully automated lazy loading, Zenith speculatively pre-loads heavyweight dependencies concurrently in background threads, enabling near-instantaneous application boot times.

---

## Performance & Telemetry Benchmarks

Performance optimization is Zenith's core mission. The telemetry suite measures boot sequences using representative workloads (e.g., initializing `multiprocessing`, `urllib.request`, `sqlite3`, `json`, and parsed XML structures simultaneously):

### Average Boot Speed Comparison

| Load Phase | Native Python | Zenith (Warm Cache) | Absolute Savings | Relative Improvement |
| :--- | :--- | :--- | :--- | :--- |
| **Boot Duration (s)** | `~0.150s` | `~0.040s` | **0.110s** | **~73.3% faster** |
| **Boot Duration (ms)**| `~150.0ms`| `~40.0ms` | **110.0ms** | **~73.3% faster** |

*Note: Telemetry metrics are recorded on isolated subprocess iterations to prevent memory warm-up leakage.*

---

## Technical Deep Dive

Zenith accomplishes extreme startup optimization without requiring application code refactoring. It manages this through two specialized, low-level systems:

```
                  [Application Entrypoint]
                             │
                    ( zenith.ignite() )
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [sys.meta_path Interception]      [Background Thread Pool]
    - ZenithLazyFinder                - SpeculationEngine (Free-Threaded)
    - Returns ZenithLazyModule        - Pre-loads actual modules (GIL-free)
```

### 1. Interception Layer (`sys.meta_path`)
* **Custom MetaPathFinder (`ZenithLazyFinder`):** Injected at index zero of `sys.meta_path`, this hook intercept all import requests.
* **Proxy Lazy Loading (`ZenithLazyModule`):** Instead of executing synchronous, disk-bound imports, Zenith instantly returns a proxy module. The actual loading is postponed until an attribute of the module is actively accessed.

### 2. Speculative Execution (`SpeculationEngine`)
* **Background Pre-loading:** Operating concurrently to your application's bootstrap phase, a persistent background thread (`SpeculationEngine`) proactively loads modules into memory.
* **PEP 703 Multi-threading:** On Python 3.14+ free-threaded environments, this process runs on separate CPU cores completely free of the Global Interpreter Lock (GIL) overhead, avoiding main-thread performance degradation.

---

## Telemetry Suite (`zenith-check`)

Zenith includes an integrated performance verification tool under `examples/zenith_telemetry.py` to allow engineers to measure latency in their specific hardware environments.

### Running the Telemetry Script

To measure the millisecond savings on your system, execute:

```bash
python3 examples/zenith_telemetry.py
```

### Expected Output Structure

```text
=========================================
     ZENITH PERFORMANCE TELEMETRY        
=========================================
Running telemetry measurements...

-----------------------------------------
 METRIC          | NATIVE     | ZENITH   
-----------------------------------------
 Avg Boot (s)    | 0.06168s   | 0.00152s
 Avg Boot (ms)   | 61.68ms    | 1.52ms
-----------------------------------------
 Telemetry Result: Saved 60.16ms (97.5% faster)
=========================================
```

---

## ⚙️ Installation

We highly recommend installing this tool inside an isolated virtual environment to comply with modern OS security standards (PEP 668) and avoid dependency conflicts.

Please note that while the package is distributed as `alenia-zenith` on PyPI, the library is imported under the name `zenith`.

```bash
# 1. Create a virtual environment
python3 -m venv alenia_env

# 2. Activate it
# On Linux/macOS:
source alenia_env/bin/activate
# On Windows:
alenia_env\Scripts\activate

# 3. Install the engine
pip install alenia-zenith
```

Note for global installation: If you prefer a system-wide installation (e.g., inside Docker or specific CI/CD pipelines) and are aware of the risks, you can bypass the OS restriction flag:
```bash
pip install alenia-zenith --break-system-packages
```

---

## Quick Start

Initialize Zenith at the absolute top of your entrypoint script:

```python
import zenith
zenith.ignite()

# Your heavyweight imports (loaded lazily & speculatively in the background)
import pandas as pd
import numpy as np
```

---

## Configuration & Cache Persistence

Zenith automatically establishes a local import registry file in your project's root:

* **`.zenith_cache.json`:** Records module import sequences and dependencies during runtime. On subsequent boot cycles, the `SpeculationEngine` reads this cache to proactively queue modules on background threads, ensuring instant availability.

---

## License

Distributed under the ALENIA STUDIOS TOOL LICENSE Version 1.0. See [LICENSE](https://github.com/Kaia-Alenia/Zenith/blob/main/LICENSE) for more information.
