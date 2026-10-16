from __future__ import annotations

from app.models.schemas import BenchmarkItem, WorkflowRun
from benchmark.metrics.assertions import (
    assertion_category,
    assertion_group,
    assertion_need_human,
    assertion_status,
)


class RuleBasedJudge:
    name = "rule_based"

    def judge(self, item: BenchmarkItem, run: WorkflowRun) -> list:
        results = [
            assertion_category(
                "understand_agent",
                item.expected_category.value if item.expected_category else None,
                run.understood.category.value,
            ),
            assertion_group(
                "process_agent",
                item.expected_group,
                run.processed.assigned_group,
            ),
            assertion_need_human(
                "process_agent",
                item.expected_need_human,
                run.understood.need_human or run.processed.need_human,
            ),
            assertion_status(
                "workflow",
                item.expected_status.value if item.expected_status else None,
                run.ticket.status.value,
            ),
        ]
        return [result.to_result(item.case_id, judge_model=self.name) for result in results]
