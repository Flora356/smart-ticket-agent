from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.container import ApplicationContainer
from app.models.schemas import BenchmarkItem, EvaluationResult, WorkflowRun
from benchmark.judges.rule_judge import RuleBasedJudge
from benchmark.runners.loader import load_benchmark


@dataclass
class BenchmarkReport:
    total_cases: int = 0
    passed_cases: int = 0
    total_assertions: int = 0
    passed_assertions: int = 0
    results: list[EvaluationResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def case_pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return round(self.passed_cases / self.total_cases, 4)

    @property
    def assertion_pass_rate(self) -> float:
        if self.total_assertions == 0:
            return 0.0
        return round(self.passed_assertions / self.total_assertions, 4)

    def to_dict(self) -> dict:
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "total_assertions": self.total_assertions,
            "passed_assertions": self.passed_assertions,
            "case_pass_rate": self.case_pass_rate,
            "assertion_pass_rate": self.assertion_pass_rate,
            "failures": self.failures,
            "results": [result.model_dump(mode="json") for result in self.results],
        }


class BenchmarkRunner:
    def __init__(
        self,
        container: ApplicationContainer,
        *,
        judge: RuleBasedJudge | None = None,
    ) -> None:
        self.container = container
        self.judge = judge or RuleBasedJudge()

    def run_file(self, dataset_path: Path | str) -> BenchmarkReport:
        return self.run_items(load_benchmark(dataset_path))

    def run_items(self, items: list[BenchmarkItem]) -> BenchmarkReport:
        report = BenchmarkReport(total_cases=len(items))
        for item in items:
            try:
                result = self.container.workflow.run(
                    raw_content=item.input_text,
                    user_id=f"benchmark:{item.case_id}",
                )
                run = WorkflowRun(
                    ticket=result.ticket,
                    understood=result.understand,
                    processed=result.process,
                    responded=result.respond,
                    qc=result.qc,
                    trace_id=result.trace_id,
                    total_latency_ms=result.total_latency_ms,
                )
                case_results = self.judge.judge(item, run)
                report.results.extend(case_results)
                report.total_assertions += len(case_results)
                report.passed_assertions += sum(1 for r in case_results if r.passed)
                if all(r.passed for r in case_results):
                    report.passed_cases += 1
                else:
                    report.failures.append(item.case_id)
                for evaluation in case_results:
                    self.container.repository.append_eval_result(evaluation)
            except Exception as exc:
                report.failures.append(f"{item.case_id}:workflow_error:{exc}")
        return report
