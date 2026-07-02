import sys
from unittest.mock import patch, MagicMock
import pytest

from zenith.cli import main

@pytest.fixture
def mock_sys_exit():
    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
        yield mock_exit

def test_analyze_command(capsys):
    with patch("zenith.transformer.ast_rewriter.analyze_file", return_value=["os", "json", "requests"]) as mock_analyze:
        with patch("sys.argv", ["zenith", "analyze", "dummy.py"]):
            main()
        
        captured = capsys.readouterr()
        assert "[Zenith Analyzer] 'dummy.py'" in captured.out
        assert "Total imports : 3" in captured.out
        mock_analyze.assert_called_once_with("dummy.py")

def test_status_command(capsys):
    with patch("zenith.status", return_value={
            "version": "1.0.0",
            "initialized": True,
            "workers": 2,
            "preloaded_count": 5,
            "failed_count": 0,
            "cached_modules": ["os", "json"]
        }) as mock_status, patch("zenith.ignite") as mock_ignite:
        
        with patch("sys.argv", ["zenith", "status"]):
            main()
        
        captured = capsys.readouterr()
        assert "[Zenith Status] v1.0.0" in captured.out
        assert "Initialized   : True" in captured.out
        assert "Workers       : 2" in captured.out
        mock_ignite.assert_called_once_with(show_banner=False)
        mock_status.assert_called_once()

def test_invalidate_command(capsys):
    with patch("zenith.invalidate_cache") as mock_inv:
        with patch("sys.argv", ["zenith", "invalidate"]):
            main()
            
        captured = capsys.readouterr()
        assert "[Zenith] Cache invalidated." in captured.out
        mock_inv.assert_called_once()
