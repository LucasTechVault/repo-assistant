from pathlib import Path

import pytest
from pydantic import ValidationError

from repo_repair.config import Settings


def test_defaults_resolve_to_caller_directory(tmp_path: Path) -> None:
    settings = Settings()
    assert settings.repo_path == tmp_path.resolve()
    assert settings.log_level == "INFO"


def test_dotenv_loads_values_and_ignores_unrelated_keys(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "REPO_REPAIR_REPO_PATH=target\nREPO_REPAIR_LOG_LEVEL=DEBUG\nOTHER_APP=value\n",
        encoding="utf-8",
    )
    settings = Settings()
    assert settings.repo_path == (tmp_path / "target").resolve()
    assert settings.log_level == "DEBUG"


def test_environment_overrides_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("REPO_REPAIR_LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("REPO_REPAIR_LOG_LEVEL", "ERROR")
    assert Settings().log_level == "ERROR"


def test_explicit_path_overrides_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("REPO_REPAIR_REPO_PATH", "environment")
    assert Settings(repo_path=Path("explicit")).repo_path == (tmp_path / "explicit").resolve()


def test_invalid_log_level_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPO_REPAIR_LOG_LEVEL", "invalid")
    with pytest.raises(ValidationError, match="log_level"):
        Settings()


def test_home_path_is_expanded() -> None:
    assert Settings(repo_path=Path("~/target")).repo_path == (Path.home() / "target").resolve()
