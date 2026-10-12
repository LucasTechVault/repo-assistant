"""Exercise installed packaging, environment loading, and repository checks together."""

import json
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest


@pytest.mark.integration
def test_installed_cli_checks_example_from_dotenv(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    example = project_root / "examples" / "broken-python-api"
    # A space in the absolute path also exercises console argument/environment handling.
    caller = tmp_path / "caller directory"
    caller.mkdir()
    (caller / ".env").write_text(
        f'REPO_REPAIR_REPO_PATH="{example}"\nREPO_REPAIR_LOG_LEVEL=DEBUG\n',
        encoding="utf-8",
    )
    executable_name = "repo-repair.exe" if sys.platform == "win32" else "repo-repair"
    executable = Path(sysconfig.get_path("scripts")) / executable_name
    assert executable.is_file(), "Install the project with uv sync before running tests."
    result = subprocess.run(
        [str(executable), "check", "--json"],
        cwd=caller,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "repo_path": str(example),
        "is_git_repository": False,
        "has_pyproject": True,
        "has_tests": True,
    }


@pytest.mark.integration
def test_module_entry_point_reports_missing_repository(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "repo_repair", "check", "--repo", "missing"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Repository error:" in result.stderr
