import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from repo_repair import __version__
from repo_repair.app.cli import app

runner = CliRunner()


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "config" in result.output
    assert "check" in result.output


def test_version_works_even_with_invalid_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPO_REPAIR_LOG_LEVEL", "invalid")
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"repo-repair-assistant {__version__}"


def test_config_outputs_effective_values(tmp_path: Path) -> None:
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"repo_path": str(tmp_path.resolve()), "log_level": "INFO"}


def test_check_reports_markers_and_cli_path_overrides_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / "pyproject.toml").touch()
    (repo / "tests").mkdir()
    (repo / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    monkeypatch.setenv("REPO_REPAIR_REPO_PATH", "missing")
    result = runner.invoke(app, ["check", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "repo_path": str(repo.resolve()),
        "is_git_repository": True,
        "has_pyproject": True,
        "has_tests": True,
    }


def test_check_human_output(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert f"Repository directory is readable: {tmp_path.resolve()}" in result.output


@pytest.mark.parametrize("target", ["missing", "file.txt"])
def test_check_rejects_missing_paths_and_files(target: str, tmp_path: Path) -> None:
    (tmp_path / "file.txt").touch()
    result = runner.invoke(app, ["check", "--repo", target])
    assert result.exit_code == 1
    assert "Repository error:" in result.stderr


def test_invalid_config_returns_usage_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPO_REPAIR_LOG_LEVEL", "invalid-sensitive-value")
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 2
    assert "Configuration error:" in result.stderr
    assert "Traceback" not in result.output
    assert "invalid-sensitive-value" not in result.output


def test_unknown_command_returns_usage_error() -> None:
    assert runner.invoke(app, ["repair"]).exit_code == 2
