
from dataclasses import dataclass, field
from typing import Set, Optional


@dataclass
class ZenithConfig:
    workers: int = 4
    verbose: bool = False
    extra_exclusions: Set[str] = field(default_factory=set)
    cache_path: Optional[str] = None