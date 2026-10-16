from __future__ import annotations

import json
import os
import urllib.request


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible client without forcing an SDK dependency."""

    name = "openai_compatible"

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str = "",
        timeout_seconds: int = 30,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for openai_compatible provider")
        if not self.base_url:
            raise ValueError("OPENAI_BASE_URL is required for openai_compatible provider")

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
