from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    name: str
    model_name: str

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        """Generate text for the given prompt."""
