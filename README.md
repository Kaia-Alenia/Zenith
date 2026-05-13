# Zenith

[![Python Version](https://img.shields.io/badge/python-3.14%20%7C%203.15-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Alenia%20Studios%201.0-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-red.svg)](README.md)

Zero-latency boot infrastructure for Python applications.

Zenith is a deep infrastructure engine designed to eliminate startup latency in Python CLI tools, desktop applications, and serverless environments. By leveraging Python 3.14's free-threading capabilities and automated lazy loading, Zenith speculatively pre-loads your heavy dependencies in the background, resulting in near-instant application boot times.

---

## How It Works

Zenith operates transparently beneath Python's import system using two key architectural components:

1. **MetaPathFinder Interceptor (`ZenithLazyFinder`):** Implements a low-overhead import hook in `sys.meta_path` to intercept module import requests. Instead of performing slow, synchronous loading of heavy packages at boot time, it returns custom lazy modules (`ZenithLazyModule`).
2. **Speculative Pre-loading Engine (`SpeculationEngine`):** Operates on an isolated background thread utilizing **Free-Threading (PEP 703)** available in Python 3.14+. It loads heavy modules concurrently without incurring the Global Interpreter Lock (GIL) overhead, resolving dependencies before your main thread even requests them.

---

## Performance Benchmark

The following benchmark demonstrates boot time comparison when loading heavyweight libraries (such as `multiprocessing`, `urllib`, `sqlite3`, and parsed XML structures):

| Environment | Boot Time | Speedup |
| :--- | :--- | :--- |
| **Native Python** | `~0.15s` | Baseline |
| **Zenith (Warm Cache)** | `~0.04s` | **70% faster** |

---

## Installation

Please note that while the package is installed as `zenith-core`, the import statement in your Python code remains `zenith`.

```bash
pip install zenith-core
```

---

## Quick Start

Initialize Zenith at the absolute top of your application's entrypoint before any other imports:

```python
import zenith
zenith.ignite()

# Your heavy imports go here (will be processed lazily & speculatively)
import pandas
import numpy
```

---

## Configuration

Zenith automatically generates a lightweight, persistent dependency graph file in the root of your project:

* **`.zenith_cache.json`:** This file records actual module usage during execution. On subsequent boots, the `SpeculationEngine` reads this cache to proactively queue and pre-load modules on background threads, ensuring instant availability.

---

## License

Distributed under the ALENIA STUDIOS TOOL LICENSE Version 1.0. See LICENSE for more information.
