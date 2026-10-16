from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import BenchmarkItem


def load_benchmark(path: Path | str) -> list[BenchmarkItem]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"benchmark dataset not found: {dataset_path}")

    items: list[BenchmarkItem] = []
    for line_number, raw_line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            items.append(BenchmarkItem.model_validate_json(line))
        except Exception as exc:
            raise ValueError(
                f"invalid benchmark item at {dataset_path}:{line_number}: {exc}"
            ) from exc
    return items
