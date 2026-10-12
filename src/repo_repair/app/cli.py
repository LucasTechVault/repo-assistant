"""M00 CLI: show configuration and validate a repository directory."""

import json
import os
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from repo_repair import __version__
from repo_repair.config import Settings

app = typer.Typer(
    name="repo-repair",
    help="Repo Repair Assistant: M00 configuration and repository checks.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"repo-repair-assistant {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """Provide application-wide options."""


def _settings(repo: Path | None = None) -> Settings:
    try:
        return Settings() if repo is None else Settings(repo_path=repo)
    except (ValidationError, OSError, RuntimeError) as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command("config")
def show_config() -> None:
    """Print the effective M00 configuration as JSON."""
    typer.echo(_settings().model_dump_json(indent=2))


@app.command()
def check(
    repo: Annotated[
        Path | None,
        typer.Option("--repo", "-r", help="Directory to check; overrides REPO_REPAIR_REPO_PATH."),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print a machine-readable summary.")
    ] = False,
) -> None:
    """Check that a directory exists and report its project markers without executing code."""
    settings = _settings(repo)
    path = settings.repo_path
    try:
        if not path.is_dir():
            typer.echo(
                f"Repository error: directory does not exist or is not a directory: {path}",
                err=True,
            )
            raise typer.Exit(code=1)
        # Probe readability without modifying the repository or running its code.
        with os.scandir(path):
            pass
        summary = {
            "repo_path": str(path),
            "is_git_repository": (path / ".git").exists(),
            "has_pyproject": (path / "pyproject.toml").is_file(),
            "has_tests": (path / "tests").is_dir(),
        }
    except OSError as exc:
        typer.echo(f"Repository error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(summary, indent=2))
    else:
        typer.echo(f"Repository directory is readable: {path}")
        typer.echo(f"Git marker: {summary['is_git_repository']}")
        typer.echo(f"Python project: {summary['has_pyproject']}")
        typer.echo(f"Tests directory: {summary['has_tests']}")
