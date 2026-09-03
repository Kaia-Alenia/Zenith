import sys
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from zenith.models import ImportMeasurement, MeasurementSource

@dataclass
class ProfileResult:
    target_args: List[str]
    exit_code: int
    measurements: List[ImportMeasurement]
    stderr_passthrough: str

def parse_importtime(stderr: str) -> Tuple[List[ImportMeasurement], str]:
    # Regex to match the Python 3.10+ importtime format
    # format: import time: self [us] | cumulative | imported package
    lines = stderr.splitlines()
    measurements = []
    passthrough = []
    
    parsing = False
    for line in lines:
        if line.startswith("import time: self [us] | cumulative | imported package"):
            parsing = True
            continue
            
        if parsing and line.startswith("import time:"):
            # Example: "import time:      1150 |       1150 |   _io"
            # Or nested: "import time:      1000 |       2000 |     _io"
            parts = line[12:].split("|")
            if len(parts) == 3:
                try:
                    self_us = int(parts[0].strip())
                    cum_us = int(parts[1].strip())
                    name_part = parts[2].rstrip()
                    # Count leading spaces for depth. Each depth level seems to add 2 spaces.
                    # But wait, leading spaces might be padded before the name.
                    depth_str = parts[2].replace(parts[2].lstrip(), '')
                    depth = len(depth_str) // 2
                    name = parts[2].strip()
                    
                    measurements.append(ImportMeasurement(
                        module=name,
                        self_time_ns=self_us * 1000,
                        cumulative_time_ns=cum_us * 1000,
                        depth=depth,
                        success=True,
                        source=MeasurementSource.CPYTHON_IMPORTTIME
                    ))
                except ValueError:
                    passthrough.append(line)
        else:
            passthrough.append(line)
            
    return measurements, "\n".join(passthrough)

def profile_target(args: List[str]) -> ProfileResult:
    # Run with -X importtime
    cmd = [sys.executable, "-X", "importtime"] + args
    
    # We pipe stderr to capture importtime, but it might contain app errors too.
    # We let stdout pass through to the real stdout.
    result = subprocess.run(cmd, stdout=sys.stdout, stderr=subprocess.PIPE, text=True)
    
    measurements, passthrough = parse_importtime(result.stderr)
    
    return ProfileResult(
        target_args=args,
        exit_code=result.returncode,
        measurements=measurements,
        stderr_passthrough=passthrough
    )
