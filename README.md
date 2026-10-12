# Repo Repair Assistant

A standalone learning project for building a repository repair assistant from scratch.
**M00 is complete bootstrap infrastructure:** an installable Python package, validated
configuration, a useful CLI, and a tested example defect. Automated repair belongs to later
milestones.

## Quick start

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12.
The project pins the 3.12 minor line; uv can install it if it is missing.

From this repository directory:

```sh
uv sync --locked
uv run repo-repair --help
uv run repo-repair --version
uv run repo-repair check --repo examples/broken-python-api
uv run repo-repair check --repo examples/broken-python-api --json
```

The equivalent module entry point is `uv run python -m repo_repair`.
Both entry points work from another directory after installation; configuration is resolved
relative to the caller's current directory.

## Configuration

```sh
cp .env.example .env
uv run repo-repair config
uv run repo-repair check
```

| Setting | Default | Meaning |
| --- | --- | --- |
| `REPO_REPAIR_REPO_PATH` | `.` | Directory to check; relative paths use the caller's cwd. |
| `REPO_REPAIR_LOG_LEVEL` | `INFO` | Validated verbosity setting reserved for later logging. |

Accepted log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (uppercase).
Priority: explicit `check --repo` > environment > `.env` in the current directory > defaults.
The CLI does not search parent directories for `.env`. Unrelated dotenv keys are ignored.
`config` prints the effective M00 fields as JSON; invalid settings return exit code 2.

`check` verifies that the path is a readable directory and reports `.git`, `pyproject.toml`,
and `tests` markers. A directory without these markers is still valid. The Git field reports
a marker at this directory, including worktree `.git` files; it does not validate Git metadata
or search ancestor directories. Missing, unreadable, or file paths return exit code 1.
Successful commands return 0. Usage/configuration errors return 2.

## Development checks

```sh
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

For intentional edits, format with `uv run ruff format .`.
Commit `uv.lock` to preserve the tested dependency versions. `uv sync --locked` refuses an
out-of-date lockfile. A lock update is an explicit maintenance operation (`uv lock`).

The default pytest suite collects **only `tests/`**, keeping the known broken example out
of the M00 baseline. Strict mypy and Ruff cover both the application and the example.
The integration tests execute the installed `repo-repair` script and the module entry point
in fresh processes, including configuration loaded from a different working directory.

## Deliberately broken example

`examples/broken-python-api` is a separate Python project with its own test configuration
and no dependency on the assistant. Its `create_order(quantity)` returns an order without
checking that the quantity is positive. It is a minimal API domain function, with no HTTP
server or framework needed.

Run the example explicitly, using the main project's installed test runner:

```sh
uv run pytest -c examples/broken-python-api/pyproject.toml examples/broken-python-api/tests
```

**Expected: 1 passed, 3 failed, exit code 1.** The regression cases `0`, `-1`, and `-10` expect
`ValueError`, but the broken function does not raise. They are real failures, with no skip
or `xfail` marker. Leave the defect in place for a later repair milestone.

The positive baseline can be run separately:

```sh
uv run pytest -c examples/broken-python-api/pyproject.toml examples/broken-python-api/tests -k accepts_positive
```

The example also runs independently:

```sh
cd examples/broken-python-api
uv sync --locked
uv run pytest
```

## Layout and M00 boundaries

```text
src/repo_repair/
  __init__.py           # installed package version
  __main__.py           # python -m entry point
  config.py             # Pydantic Settings
  app/cli.py            # Typer commands
  py.typed              # typed package marker
tests/
  test_config.py
  test_cli.py
  integration/test_cli_end_to_end.py
examples/broken-python-api/
  pyproject.toml
  src/broken_python_api/orders.py
  tests/test_orders.py
```

The original `High_Level_System_Architecture.md` is preserved as a future design reference.
M00 implements the application/configuration boundary only. There is no agent runtime,
model gateway, context engine, tool registry, subprocess test runner in the application,
patching, or repair workflow. Configuration construction has no write side effects;
the CLI does not execute target repository code or modify files.

See [M00 contracts](docs/M00.md) for the implemented interfaces and
[verification results](docs/verification.md) for recorded checks.
