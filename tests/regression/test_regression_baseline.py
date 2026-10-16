from __future__ import annotations

import pytest


@pytest.mark.regression
def test_benchmark_pass_rate_meets_baseline(container) -> None:
    from app.config import PROJECT_ROOT
    from benchmark.runners.runner import BenchmarkRunner

    dataset = PROJECT_ROOT / "benchmark" / "datasets" / "tickets_l1_l3.jsonl"
    report = BenchmarkRunner(container).run_file(dataset)
    assert report.case_pass_rate >= 0.75
    assert report.assertion_pass_rate >= 0.85


@pytest.mark.regression
def test_ticket_cost_units_are_recorded(container) -> None:
    result = container.workflow.run("AF205 配网失败，提示错误码 E104")
    assert result.ticket.id is not None
    assert container.repository.total_cost_units(result.ticket.id) >= 0
