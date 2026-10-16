from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AppConfig:
    database_path: Path
    max_retries: int = 2
    confidence_threshold: float = 0.55
    auto_reply_enabled: bool = True
    provider_name: str = "rule_based"
    model_name: str = "local-rule-engine"
    base_url: str = ""
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls, overrides: dict[str, str] | None = None) -> AppConfig:
        overrides = overrides or {}
        raw_db = overrides.get("database_path") or os.getenv(
            "TICKET_AGENT_DB", "ticket_agent.db"
        )
        db_path = Path(raw_db)
        if not db_path.is_absolute():
            db_path = PROJECT_ROOT / db_path

        return cls(
            database_path=db_path,
            max_retries=int(
                overrides.get("max_retries", os.getenv("TICKET_AGENT_MAX_RETRIES", "2"))
            ),
            confidence_threshold=float(
                overrides.get(
                    "confidence_threshold",
                    os.getenv("TICKET_AGENT_CONFIDENCE_THRESHOLD", "0.55"),
                )
            ),
            auto_reply_enabled=(
                overrides.get(
                    "auto_reply_enabled",
                    os.getenv("TICKET_AGENT_AUTO_REPLY", "true"),
                ).lower()
                == "true"
            ),
            provider_name=overrides.get(
                "provider_name",
                os.getenv("TICKET_AGENT_PROVIDER", "rule_based"),
            ),
            model_name=overrides.get(
                "model_name",
                os.getenv("TICKET_AGENT_MODEL", "local-rule-engine"),
            ),
            base_url=overrides.get("base_url", os.getenv("OPENAI_BASE_URL", "")),
            timeout_seconds=int(
                overrides.get("timeout_seconds", os.getenv("TICKET_AGENT_TIMEOUT", "30"))
            ),
        )

    def with_database(self, database_path: Path | str) -> AppConfig:
        return replace(self, database_path=Path(database_path))
