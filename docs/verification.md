# M00 verification

Verified on 12 October 2026 (Asia/Singapore) in the requested repository.
Environment: macOS arm64, CPython 3.12.8, uv 0.12.3.

| Check | Actual command | Result |
| --- | --- | --- |
| Reproducible main install | `uv sync --locked` | Exit 0; lockfile current. |
| Formatting | `.venv/bin/ruff format --check .` | Exit 0; 16 files already formatted. |
| Lint | `.venv/bin/ruff check .` | Exit 0; all checks passed. |
| Strict types | `.venv/bin/mypy` | Exit 0; no issues in 12 source files. |
| Main tests | `.venv/bin/pytest` | Exit 0; 17 passed, no warnings. |
| Distribution build | `uv build` | Exit 0; wheel and source distribution built. |
| Example suite, from main root | `.venv/bin/pytest -c examples/broken-python-api/pyproject.toml examples/broken-python-api/tests` | Exit 1; 1 passed, 3 failed as intended. |
| Example standalone, from its directory | `uv run --locked pytest` | Exit 1; 1 passed, 3 failed as intended. |

The failing example quantities are `0`, `-1`, and `-10`; each failure is
`DID NOT RAISE ValueError`. No example regressions are skipped or marked `xfail`.

The main suite includes 6 configuration cases, 9 CLI cases, and 2 process-level integration
cases. It verifies configuration priority, cwd and home path resolution, validation errors,
CLI help/version/JSON/human output, missing/file paths, installed console script behavior,
and the module entry point. The example is excluded by the main `testpaths = ["tests"]`.

Locked tool versions: Ruff 0.17.0, mypy 1.20.2, pytest 9.1.1, Typer 0.27.3,
Pydantic 2.14.1, Pydantic Settings 2.15.0.

The original architecture document was preserved. M00 files are left uncommitted for review.
No later milestone components were implemented.
