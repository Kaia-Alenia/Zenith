import sys
from unittest.mock import patch
import pytest

from zenith.cli import main

def test_status_command(capsys):
    with patch("sys.argv", ["zenith", "status"]):
        main()
    captured = capsys.readouterr()
    assert "[Zenith Status]" in captured.out
    
def test_cache_command(capsys):
    with patch("sys.argv", ["zenith", "cache"]):
        main()
    captured = capsys.readouterr()
    assert "Cache management" in captured.out
