from __future__ import annotations

from app.config import AppConfig
from app.providers.base import LLMProvider
from app.providers.rule_based import RuleBasedProvider


def build_provider(config: AppConfig) -> LLMProvider:
    if config.provider_name == "rule_based":
        return RuleBasedProvider(model_name=config.model_name)
    if config.provider_name == "openai_compatible":
        from app.providers.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(
            model_name=config.model_name,
            base_url=config.base_url,
            timeout_seconds=config.timeout_seconds,
        )
    raise ValueError(f"unsupported provider: {config.provider_name}")
