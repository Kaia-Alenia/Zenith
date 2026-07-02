<div align="center">
  <h1>🚀 Zenith</h1>
  <p><b>Startup optimization library for Python applications.</b></p>
  
  [![PyPI Version](https://img.shields.io/pypi/v/alenia-zenith.svg?color=blueviolet)](https://pypi.org/project/alenia-zenith/)
  [![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-darkviolet.svg)](https://github.com/Kaia-Alenia/alenia-zenith)
  [![License](https://img.shields.io/badge/License-Alenia%20Studios%20Tool%201.0-8a2be2.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-indigo.svg)](#)
  
  *Read this in [Spanish (Español)](README-es.md).*
</div>

---

Zenith reduces your application's import time by combining **lazy import proxies** (modules are not executed until first attribute access) and **speculative background pre-loading** (a thread pool pre-loads known modules while your app boots). A persistent cache learns which modules your app uses across runs, making every subsequent boot faster.

> **Why Zenith?** Python 3.15 introduces lazy imports, but Zenith actively *pre-loads* modules in the background based on run history, so they are ready before you access them.

## ✨ Key Features & Use Cases

* ⚡ **Command Line Interfaces (CLIs):** Deliver sub-second launch times for tools where a startup latency of 200ms+ ruins user experience.
* ☁️ **Serverless APIs (Cold Starts):** Drastically reduce cold starts in serverless environments (AWS Lambda, Google Cloud Run) by allowing the server to bind and listen immediately.
* 📊 **Data Science & ML Pipelines:** Bypass the initialization lag of heavy packages (`pandas`, `numpy`, `torch`) during frequent script executions.
* 🖥️ **Desktop / GUI Applications:** Improve perceived performance by launching the main interface instantly while loading secondary libraries asynchronously.

## 📈 Benchmarks

Benchmarks run on isolated subprocesses (5 runs averaged) loading heavy standard and third-party libraries:

| Metric          | Native Python | Zenith (warm) | Improvement |
|:----------------|:-------------:|:-------------:|:-----------:|
| Avg Boot (ms)   | ~52ms         | ~37ms         | **~28%** 🚀 |

*(Note: First run builds the cache. Subsequent runs benefit from speculative pre-loading. Results vary by hardware and module set.)*

## 🛠️ Installation

```bash
pip install alenia-zenith
```
*For system-wide use (Docker, CI/CD), append `--break-system-packages`.*

## 🚀 Quick Start

Initialize Zenith at the very top of your application entrypoint:

```python
import zenith
zenith.ignite()

# Your imports — served lazily and pre-loaded in the background
import pandas as pd
import numpy as np
import requests
```

### Advanced Initialization

```python
import zenith

zenith.ignite(
    file=__file__,                    # Scan this file's imports and pre-load them
    workers=8,                        # Background thread pool size (default: 4)
    verbose=True,                     # Print pre-load events to stdout
    exclude=["mymodule", "django"],   # Never lazy-load these packages
    cache_path=".cache/zenith.json",  # Custom cache location
    show_banner=False,                # Suppress the ASCII banner
)

# Explicitly pre-load specific modules
zenith.warm("pandas", "numpy", "torch")
```

## ⚙️ How It Works

1. **Lazy Import Hook**: Inserts a proxy system into `sys.meta_path`. `import` statements return a lightweight `ZenithLazyModule` instead of executing immediately.
2. **Speculative Pre-loader**: A `ThreadPoolExecutor` pre-loads cached modules in background threads, bypassing the proxy system to load real modules.
3. **Persistent Cache**: On exit, Zenith saves the used modules to `.zenith_cache.json` to accelerate future executions.

## 💻 CLI Tools

Zenith provides a built-in CLI for diagnostics and benchmarking:

```bash
# Analyze imports in a file
zenith analyze myapp/main.py --verbose

# Show cache status
zenith status

# Run a benchmark comparison
zenith benchmark --runs 5 --modules pandas numpy requests

# Clear the cache
zenith invalidate
```

## ⚠️ Known Limitations

- **GIL:** Zenith uses standard threading. Background threads share the GIL with the main thread, making pre-loading concurrent, not parallel. Speedups come from overlapping I/O-bound disk reads.
- **Cold First Run:** The first run has no cache and shows no speedup. The magic happens from the second run onward.
- **C Extensions:** Some C extension modules are not safe to import from a background thread. Use `zenith.exclude("module_name")` for those.

## 📜 License

Distributed under the GNU General Public License v3 (GPL v3). See [LICENSE](LICENSE) for more information.

Contact: contact.aleniastudios@gmail.com
