class ZenithError(Exception):
    """Base exception for all Zenith errors."""
    pass

class ZenithConfigurationError(ZenithError):
    """Raised when Zenith configuration is invalid or conflicting."""
    pass

class ZenithProfileError(ZenithError):
    """Raised when there is an error during profiling."""
    pass

class ZenithCacheError(ZenithError):
    """Raised when there is an error reading or writing the cache."""
    pass

class ZenithBackendError(ZenithError):
    """Raised when an optimization backend encounters a fatal error."""
    pass
