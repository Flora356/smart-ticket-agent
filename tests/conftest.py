from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

import pytest

from app.config import AppConfig
from app.container import ApplicationContainer


@pytest.fixture()
def temp_project_dir() -> Path:
    path = Path(mkdtemp(prefix="ticket-agent-tests-", dir=Path(__file__).resolve().parent))
    try:
        yield path
    finally:
        rmtree(path, ignore_errors=True)


@pytest.fixture()
def app_config(temp_project_dir: Path) -> AppConfig:
    return AppConfig.from_env(
        {
            "database_path": str(temp_project_dir / "test_ticket_agent.db"),
            "provider_name": "rule_based",
            "model_name": "local-rule-engine",
        }
    )


@pytest.fixture()
def container(app_config: AppConfig):
    app = ApplicationContainer(app_config)
    try:
        yield app
    finally:
        app.close()
