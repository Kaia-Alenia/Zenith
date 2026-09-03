# Zenith 2.0

An adaptive, observable and conservative startup optimization framework for Python applications.

## What is Zenith?
Zenith optimizes the **startup path** of Python applications. It learns from repeated runs, identifies safe optimization strategies, and applies them (like `PRELOAD` or `LAZY`) to reduce startup time safely.

## Installation
Currently in development.

## Usage
```python
import zenith

# Initialize with SAFE mode
zenith.ignite(zenith.ZenithConfig(mode="safe"))

# ... your application initialization ...

# Mark the readiness boundary
zenith.mark_ready()
```

## Modes
- **PROFILE**: Measure and analyze with normal import semantics.
- **SAFE**: Runtime learning and explicitly safe optimizations without global lazy interception (default).
- **LAZY**: Enable lazy loading for explicitly eligible modules.
- **ADAPTIVE**: Use accumulated evidence to select EAGER, PRELOAD, LAZY or PROTECTED.

## CLI
```bash
zenith status
zenith profile app.py
zenith analyze app.py
```
