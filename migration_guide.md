# Migration to Zenith 2.0

## API Changes
Zenith 2.0 has an entirely new API.
- Use `zenith.ignite(zenith.ZenithConfig(mode="safe"))` instead of the old configuration API.
- The `warm`, `exclude`, `analyze`, `invalidate_cache`, `explain` methods have been removed or consolidated into the new core framework.

## Modeless to Modes
You now must explicitly declare a `mode` (`PROFILE`, `SAFE`, `LAZY`, `ADAPTIVE`) through `ZenithConfig`.

## Architecture
Zenith 2.0 focuses on observation and strategy rather than purely lazy loading. Lazy loading is now an optional execution backend.
