from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import EvaluationResult


@dataclass(frozen=True)
class Metric:
    agent_name: str
    metric_name: str
    score: float
    passed: bool
    reason: str

    def to_result(
        self, case_id: str, *, judge_model: str = "rule_based"
    ) -> EvaluationResult:
        return EvaluationResult(
            case_id=case_id,
            agent_name=self.agent_name,
            metric_name=self.metric_name,
            score=max(0.0, min(self.score, 1.0)),
            passed=self.passed,
            reason=self.reason,
            judge_model=judge_model,
        )


def score_schema(agent_name: str, expected_names: set[str], actual: dict) -> Metric:
    actual_names = set(actual)
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    passed = not missing and not extra
    return Metric(
        agent_name=agent_name,
        metric_name="schema_compliance",
        score=1.0 if passed else 0.0,
        passed=passed,
        reason=f"missing={missing}; extra={extra}",
    )


def assertion_category(
    agent_name: str, expected: str | None, actual: str | None
) -> Metric:
    if expected is None:
        return Metric(agent_name, "category_match", 1.0, True, "no expectation")
    passed = expected == actual
    return Metric(
        agent_name,
        "category_match",
        1.0 if passed else 0.0,
        passed,
        f"expected={expected}; actual={actual}",
    )


def assertion_priority(
    agent_name: str, expected: str | None, actual: str | None
) -> Metric:
    if expected is None:
        return Metric(agent_name, "priority_match", 1.0, True, "no expectation")
    passed = expected == actual
    return Metric(
        agent_name,
        "priority_match",
        1.0 if passed else 0.0,
        passed,
        f"expected={expected}; actual={actual}",
    )


def assertion_group(
    agent_name: str, expected: str | None, actual: str | None
) -> Metric:
    if expected is None:
        return Metric(agent_name, "route_match", 1.0, True, "no expectation")
    passed = expected == actual
    return Metric(
        agent_name,
        "route_match",
        1.0 if passed else 0.0,
        passed,
        f"expected={expected}; actual={actual}",
    )


def assertion_need_human(
    agent_name: str, expected: bool | None, actual: bool | None
) -> Metric:
    if expected is None:
        return Metric(agent_name, "need_human_match", 1.0, True, "no expectation")
    passed = expected == actual
    return Metric(
        agent_name,
        "need_human_match",
        1.0 if passed else 0.0,
        passed,
        f"expected={expected}; actual={actual}",
    )


def assertion_status(
    agent_name: str, expected: str | None, actual: str | None
) -> Metric:
    if expected is None:
        return Metric(agent_name, "status_match", 1.0, True, "no expectation")
    passed = expected == actual
    return Metric(
        agent_name,
        "status_match",
        1.0 if passed else 0.0,
        passed,
        f"expected={expected}; actual={actual}",
    )
