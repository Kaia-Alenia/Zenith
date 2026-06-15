# Changelog — alenia-zenith

All notable changes to this project will be documented in this file.

## [1.2.2] — 2026-06-15

### Changed
- Updated README badges layout to use unified purple palette and HTML GitGem badge for PyPI synchronization.

---

## [1.2.1] — 2026-06-15

### Fixed
- Fixed memory leaks by clearing proxy loader attributes post-load.
- Added reentrancy guards for thread-lock safety.
- Implemented memory caching to avoid redundant disk reads.

### Changed
- Added GitGem verification badge to `README.md`.

---

## [1.2.0] — 2026-05-15

### Added
- `analyze_stdlib_only()` and `analyze_third_party()` functions in `ast_rewriter.py`.
- `zenith analyze`, `zenith status`, `zenith benchmark`, `zenith invalidate` CLI subcommands.
- `show_banner` parameter in `ignite()` to suppress ASCII art in library use.
- `cache_path` parameter in `ignite()` for custom cache file locations.
- `on_reconnect` callback support in the speculative pre-loader.
- Full thread-safety audit of `ZenithLazyModule` via `RLock`.

### Changed
- `ZenithLazyFinder` now uses `_active_searches` class-level set to prevent infinite finder recursion.
- Development status updated from Alpha to Beta — test coverage is now 100%.
- `benchmark.py` now uses only stdlib modules (no cross-library dependencies).

### Fixed
- `_bypass_lazy` thread-local flag now correctly prevents background threads from creating proxy chains.
- `persist_cache()` now merges existing cache with new session data instead of overwriting.

---

## [1.1.0] — 2026-04-10

### Added
- `zenith.warm(*modules)` for explicit module pre-loading.
- `zenith.exclude(*modules)` for blocking specific packages from lazy loading.
- `zenith.analyze(file)` public function wrapping AST import scanning.
- `zenith.invalidate_cache()` to clear the persistent module cache.
- `ImportPredictor` — persistent JSON cache of per-session module usage.

### Changed
- `SpeculationEngine` now uses `ThreadPoolExecutor` with configurable worker count.

---

## [1.0.0] — 2026-03-20

### Added
- Initial release of `alenia-zenith`.
- `zenith.ignite()` — one-call startup optimizer.
- `ZenithLazyFinder` / `ZenithLazyModule` / `ZenithLazyLoader` — lazy import proxy system.
- `SpeculationEngine` — background thread pool for speculative module pre-loading.
- `_bypass_lazy` thread-local flag to prevent recursive proxy loading.
- Cross-platform support: Linux, macOS, Windows (Python 3.10+).
