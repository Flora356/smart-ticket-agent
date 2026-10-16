from __future__ import annotations

from typing import Protocol

from app.models.schemas import BenchmarkItem, WorkflowRun


class Judge(Protocol):
    name: str

    def judge(self, item: BenchmarkItem, run: WorkflowRun) -> list:
        """Return a list of EvaluationResult."""
