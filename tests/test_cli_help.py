import os
import subprocess
import sys


def _run_cli_help(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp949"
    env["PYTHONUTF8"] = "0"
    return subprocess.run(
        [sys.executable, "-m", "hydra.cli.app", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_root_help_renders_without_unicode_error():
    result = _run_cli_help("--help")
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout


def test_kill_help_renders_without_unicode_error():
    result = _run_cli_help("kill", "--help")
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
