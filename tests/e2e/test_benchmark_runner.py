from __future__ import annotations

from pathlib import Path

import pytest

from app.config import PROJECT_ROOT
from benchmark.runners.runner import BenchmarkRunner


@pytest.mark.e2e
def test_l1_l3_benchmark_runs_without_workflow_errors(container) -> None:
    dataset = PROJECT_ROOT / "benchmark" / "datasets" / "tickets_l1_l3.jsonl"
    report = BenchmarkRunner(container).run_file(dataset)
    assert report.total_cases == 9
    assert report.total_assertions >= report.total_cases * 3
    assert not any("workflow_error" in failure for failure in report.failures)


@pytest.mark.e2e
def test_benchmark_report_is_serializable(container) -> None:
    dataset = PROJECT_ROOT / "benchmark" / "datasets" / "tickets_l1_l3.jsonl"
    report = BenchmarkRunner(container).run_file(dataset)
    payload = report.to_dict()
    assert "case_pass_rate" in payload
    assert "results" in payload
