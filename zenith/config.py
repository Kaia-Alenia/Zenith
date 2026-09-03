from dataclasses import dataclass, field
from typing import Optional, Sequence
from .models import Mode
from .exceptions import ZenithConfigurationError

@dataclass
class ZenithConfig:
    mode: Mode = Mode.SAFE
    workers: Optional[int] = None
    cache_path: Optional[str] = None
    exclude: Sequence[str] = field(default_factory=tuple)
    include: Sequence[str] = field(default_factory=tuple)
    verbose: bool = False
    early_process_window: float = 2.0
    background_preload: bool = True
    
    def __post_init__(self):
        if not isinstance(self.mode, Mode):
            try:
                self.mode = Mode(self.mode)
            except ValueError:
                raise ZenithConfigurationError(f"Invalid mode: {self.mode}")
        
        if self.workers is not None and self.workers < 1:
            raise ZenithConfigurationError("workers must be at least 1 if specified")
        
        if self.early_process_window < 0:
            raise ZenithConfigurationError("early_process_window must be non-negative")
