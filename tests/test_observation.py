import pytest
from zenith.observation.importtime import parse_importtime
from zenith.models import MeasurementSource

def test_parse_importtime():
    sample_stderr = """import time: self [us] | cumulative | imported package
import time:       112 |        112 | _io
import time:        50 |         50 |   marshal
import time:      1000 |       1162 | posix
some target stderr output
import time:       200 |        200 |     nested
"""
    measurements, passthrough = parse_importtime(sample_stderr)
    
    assert "some target stderr output" in passthrough
    assert "import time" not in passthrough
    
    assert len(measurements) == 4
    
    assert measurements[0].module == "_io"
    assert measurements[0].self_time_ns == 112000
    assert measurements[0].cumulative_time_ns == 112000
    assert measurements[0].depth == 0
    assert measurements[0].source == MeasurementSource.CPYTHON_IMPORTTIME
    
    assert measurements[1].module == "marshal"
    assert measurements[1].depth == 1
    
    assert measurements[3].module == "nested"
    assert measurements[3].depth == 2
