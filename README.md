# Zenith

[![PyPI Version](https://img.shields.io/pypi/v/alenia-zenith.svg?color=blueviolet)](https://pypi.org/project/alenia-zenith/)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-darkviolet.svg)](https://github.com/Kaia-Alenia/alenia-zenith)
[![License](https://img.shields.io/badge/License-Alenia%20Studios%20Tool%201.0-8a2be2.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-indigo.svg)](#)
<a href="https://gitgem.org/github/Kaia-Alenia/alenia-zenith"><img src="https://gitgem.org/api/badge/github/Kaia-Alenia/alenia-zenith.svg" alt="GitGem"></a>

**Startup optimization library for Python applications.**

Zenith reduces your application's import time by combining two mechanisms: **lazy import proxies** (modules are not executed until first attribute access) and **speculative background pre-loading** (a thread pool pre-loads known modules while your app boots). A persistent cache learns which modules your app uses across runs, making every subsequent boot faster.

> **Compared to Python 3.15 lazy imports:** Python 3.15 will defer imports until first use. Zenith goes a step further — it *actively pre-loads* those modules in the background based on your run history, so they are ready before you even access them.

---

## What is Zenith for?

Zenith is designed for Python applications that suffer from slow startup times (boot lag) caused by importing heavy libraries (such as `pandas`, `numpy`, `tensorflow`, `torch`, `click`, `rich`, or `PyQt`).

Instead of waiting for every library to load sequentially on startup, Zenith creates a fast lazy proxy system and speculatively pre-loads your dependencies in background threads using a persistent cache from previous runs.

### Core Use Cases:
* **Command Line Interfaces (CLIs):** Deliver sub-second launch times for tools where a startup latency of 200ms+ ruins user experience.
* **Serverless APIs (Cold Starts):** Drastically reduce cold starts in serverless environments (AWS Lambda, Google Cloud Run) by allowing the server to bind and listen to requests immediately while libraries load concurrently in the background.
* **Data Science & ML Pipelines:** Bypass the initialization lag of heavy packages during frequent script executions and development loops.
* **Desktop / GUI Applications:** Improve perceived performance by launching the main interface instantly while loading secondary assets and libraries asynchronously.

---


## Measured Results (warm cache)

Benchmarks run on isolated subprocesses, 5 runs averaged, loading `multiprocessing`, `urllib.request`, `sqlite3`, `json`, `xml.etree.ElementTree`:

| Metric          | Native Python | Zenith (warm) | Saved     |
|:----------------|:-------------:|:-------------:|:---------:|
| Avg Boot (ms)   | ~52ms         | ~37ms         | ~15ms     |
| Improvement     | —             | —             | **~28%**  |

> First run builds the cache. Subsequent runs benefit from speculative pre-loading. Results vary by hardware and module set.

---

## How It Works

```
              [Application Entrypoint]
                         │
               ( zenith.ignite() )
                         │
         ┌───────────────┴──────────────────┐
         ▼                                  ▼
[sys.meta_path Hook]              [ThreadPoolExecutor]
 ZenithLazyFinder                  workers=4 (default)
 Returns proxy module              Pre-loads cached modules
 on first import                   with GIL bypass per thread
         │                                  │
         ▼                                  ▼
[First attribute access]          [Module ready in sys.modules]
 _zenith_load_module() called      Main thread gets real module
 Loads real module on demand       instantly on access
```

### 1. Lazy Import Hook

`ZenithLazyFinder` is inserted at index 0 of `sys.meta_path`. Every new `import` statement returns a lightweight `ZenithLazyModule` proxy instead of executing the module immediately. The real module is only loaded the first time one of its attributes is accessed.

### 2. Speculative Pre-loader

A `ThreadPoolExecutor` (4 workers by default) pre-loads modules from the persistent cache in background threads. A thread-local bypass flag prevents background threads from creating further lazy proxies, ensuring they load real modules.

### 3. Persistent Cache

On exit, Zenith writes `.zenith_cache.json` with the list of modules used during the session. On next launch, those modules are queued for background pre-loading before user code runs.

---

## Installation

```bash
python3 -m venv alenia_env
source alenia_env/bin/activate
pip install alenia-zenith
```

For system-wide use (Docker, CI/CD):

```bash
pip install alenia-zenith --break-system-packages
```

---

## Quick Start

```python
import zenith
zenith.ignite()

# Your imports — served lazily and pre-loaded in background
import pandas as pd
import numpy as np
import requests
```

### With file-based AST scanning

```python
import zenith
zenith.ignite(file=__file__)  # Scans this file for imports and pre-loads them
```

### Full options

```python
zenith.ignite(
    file=__file__,        # Scan this file's imports and pre-load them
    workers=8,            # Background thread pool size (default: 4)
    verbose=True,         # Print pre-load events to stdout
    exclude=["mymodule"], # Never lazy-load these packages
    cache_path=".cache/zenith.json",  # Custom cache location
    show_banner=False,    # Suppress the ASCII banner
)
```

---

## Additional API

```python
# Explicitly pre-load specific modules
zenith.warm("pandas", "numpy", "torch")

# Exclude packages from lazy loading
zenith.exclude("my_c_extension", "greenlet")

# Inspect current state
info = zenith.status()
# {
#   "version": "1.2.7",
#   "initialized": True,
#   "workers": 4,
#   "preloaded_count": 12,
#   "cached_modules": [...],
#   ...
# }

# Statically analyze a file's imports
modules = zenith.analyze("myapp/main.py")

# Clear the module cache
zenith.invalidate_cache()
```

---

## CLI Tools

After installation, the `zenith` command is available:

```bash
# Analyze imports in a file
zenith analyze myapp/main.py --verbose

# Show cache status
zenith status

# Run a benchmark comparison
zenith benchmark --runs 5
zenith benchmark --runs 5 --modules pandas numpy requests

# Clear the cache
zenith invalidate
```

### Example CLI output

```text
[Zenith Analyzer] myapp/main.py
  Total imports : 18
  Stdlib        : 6
  Third-party   : 12

Third-party:
  - fastapi
  - pydantic
  - sqlalchemy
  ...
```

---

## Telemetry Script

```bash
python3 examples/zenith_telemetry.py
```

```text
=========================================
     ZENITH PERFORMANCE TELEMETRY
=========================================
Modules : multiprocessing, urllib.request, sqlite3, json, xml.etree.ElementTree
Runs    : 5
Running...

-----------------------------------------
 METRIC           |   NATIVE   |  ZENITH
-----------------------------------------
 Avg Boot (s)     | 0.05210s  | 0.03725s
 Avg Boot (ms)    | 52.10ms  | 37.25ms
-----------------------------------------
 Saved 14.86ms (28.5% faster)
=========================================
NOTE: On first run Zenith builds its cache. Run again for warm results.
```

---

## Recommended Use Cases

### ✅ Ideal For — High Impact

#### 1. CLIs (Command Line Interfaces)
```python
# cli.py — command line tool
import zenith
zenith.ignite(file=__file__, show_banner=False)

import click           # Loaded lazily
import rich            # Loaded lazily
import requests        # Loaded lazily
import yaml            # Loaded lazily
```
**Why it works:** CLI tools are launched thousands of times a day. Every 30ms saved is noticeable to the user. `click`, `rich`, and `requests` are heavy modules that take time to initialize.

**Real-world examples:** `pip`, `git`, `black`, `ruff`, `poetry` are tools where startup time is critical.

---

#### 2. APIs and Web Servers (Cold Starts)
```python
# main.py — FastAPI, Flask, Django
import zenith
zenith.ignite(file=__file__, workers=8, show_banner=False)

import fastapi
import pydantic
import sqlalchemy
import uvicorn
```
**Why it works:** In serverless environments (AWS Lambda, Google Cloud Run), the "cold start" is the biggest latency issue. Zenith allows the server to start serving requests while still loading secondary modules in the background.

---

#### 3. Data Science / ML Scripts
```python
# pipeline.py
import zenith
zenith.ignite(show_banner=False)
zenith.warm("pandas", "numpy", "sklearn", "matplotlib")

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
```
**Why it works:** `pandas`, `numpy`, and `torch` have some of the longest import times in the Python ecosystem (up to 500ms+ combined). With a warm cache, these are pre-loaded in the background while configuration code is running.

---

#### 4. Development Tools / DevTools
```python
# devtool.py
import zenith
zenith.ignite(file=__file__)

import ast, pathlib, json
from typing import ...
import mypy, black, isort
```
**Why it works:** Dev tools are invoked constantly (on every file save, in CI/CD). The cumulative startup overhead is significant.

---

#### 5. Desktop Applications (tkinter, PyQt, wx)
```python
# app.py
import zenith
zenith.ignite(workers=4, show_banner=False)

import tkinter as tk
import PIL
import sqlite3
```
**Why it works:** Python GUIs are notoriously slow to start. Zenith can pre-load secondary modules while the main window is initializing.

---

### ⚠️ Works But With Limitations

#### 6. Monolithic Django / Flask Applications
```python
# manage.py or wsgi.py
import zenith
zenith.ignite(show_banner=False, exclude=["django"])
# Do not apply lazy loading to Django itself — use warm() for secondary modules
zenith.warm("PIL", "boto3", "celery")
```
> **Limitation:** Django has its own app importation system. Apply Zenith **only** to external dependencies, not the framework itself.

---

#### 7. Jupyter Notebooks
```python
# First cell of the notebook
import zenith
zenith.ignite(show_banner=False)
zenith.warm("pandas", "matplotlib", "seaborn", "plotly")
```
> **Limitation:** In notebooks, the session lasts a long time, so the benefit of the warm cache is less noticeable. It's mainly useful for the initial kernel startup.

---

### ❌ Not Recommended

| Case | Reason |
|------|--------|
| **Short scripts (<1s total)** | The overhead of `ignite()` outweighs the benefit |
| **Critical C extensions** (`greenlet`, `gevent`) | Not thread-safe for background loading. Use `exclude()` |
| **Modules using `sys.modules[__name__]` at import-time** | May have unexpected behavior with proxies. Add to `exclude()` |
| **Python < 3.10** | Not supported due to type hints used |

---

## Known Limitations

- **GIL:** Zenith uses standard threading. On CPython (default), background threads share the GIL with the main thread. This means pre-loading is concurrent, not fully parallel. The benefit comes from overlapping I/O-bound disk reads with your main thread's execution.
- **Cold first run:** The first run has no cache and shows no speedup. The second run onward benefits from speculative pre-loading.
- **C extensions:** Some C extension modules are not safe to import from a background thread. Use `zenith.exclude("module_name")` for those.

---

## License

Distributed under the GNU General Public License v3 (GPL v3). See [LICENSE](LICENSE) for more information.

Contact: contact.aleniastudios@gmail.com

---

See [CHANGELOG.md](CHANGELOG.md) for the full version history.  
See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the list of contributors.  
See [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to contribute.
