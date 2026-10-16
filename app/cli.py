from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import AppConfig, PROJECT_ROOT
from app.container import ApplicationContainer


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def command_run_ticket(args: argparse.Namespace) -> int:
    config = AppConfig.from_env({"database_path": args.database})
    container = ApplicationContainer(config)
    try:
        result = container.workflow.run(args.text, user_id=args.user_id)
    finally:
        container.close()

    _print_json(
        {
            "ticket_id": result.ticket.id,
            "status": result.ticket.status.value,
            "category": result.ticket.category.value if result.ticket.category else None,
            "priority": result.ticket.priority.value if result.ticket.priority else None,
            "assigned_group": result.ticket.assigned_group,
            "final_action": result.ticket.final_action.value if result.ticket.final_action else None,
            "risk_level": result.ticket.risk_level.value if result.ticket.risk_level else None,
            "reply_draft": result.respond.reply_draft,
            "trace_id": result.trace_id,
            "total_latency_ms": result.total_latency_ms,
        }
    )
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    from benchmark.runners.runner import BenchmarkRunner

    config = AppConfig.from_env({"database_path": args.database})
    container = ApplicationContainer(config)
    dataset = Path(args.dataset)
    if not dataset.is_absolute():
        dataset = PROJECT_ROOT / dataset
    try:
        report = BenchmarkRunner(container).run_file(dataset)
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    finally:
        container.close()

    print(
        "Benchmark finished: "
        f"cases={report.passed_cases}/{report.total_cases} "
        f"case_pass_rate={report.case_pass_rate} "
        f"assertions={report.passed_assertions}/{report.total_assertions} "
        f"assertion_pass_rate={report.assertion_pass_rate}"
    )
    if report.failures:
        print("Failures:")
        for failure in report.failures:
            print(f"  - {failure}")
    print(f"Report: {output_path}")
    return 0 if not report.failures else 1


def command_show_ticket(args: argparse.Namespace) -> int:
    config = AppConfig.from_env({"database_path": args.database})
    container = ApplicationContainer(config)
    try:
        ticket = container.repository.get_ticket(args.ticket_id)
        events = container.repository.list_events(args.ticket_id)
        traces = container.repository.list_traces(args.ticket_id)
        if ticket is None:
            print(f"ticket {args.ticket_id} not found")
            return 1
        _print_json(
            {
                "ticket": ticket.model_dump(mode="json"),
                "events": [event.model_dump(mode="json") for event in events],
                "traces": [trace.model_dump(mode="json") for trace in traces],
                "cost_units": container.repository.total_cost_units(args.ticket_id),
            }
        )
    finally:
        container.close()
    return 0


def command_health(args: argparse.Namespace) -> int:
    config = AppConfig.from_env({"database_path": args.database})
    container = ApplicationContainer(config)
    try:
        _print_json(
            {
                "status": "ok",
                "provider": container.provider.name,
                "model": container.provider.model_name,
                "database": str(container.repository.database_path),
                "status_counts": container.repository.status_counts(),
            }
        )
    finally:
        container.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ticket-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-ticket", help="run one ticket through workflow")
    run_parser.add_argument("--text", required=True)
    run_parser.add_argument("--user-id", default="anonymous")
    run_parser.add_argument("--database", default="ticket_agent.db")
    run_parser.set_defaults(func=command_run_ticket)

    benchmark_parser = subparsers.add_parser("benchmark", help="run benchmark dataset")
    benchmark_parser.add_argument(
        "--dataset",
        default="benchmark/datasets/tickets_l1_l3.jsonl",
    )
    benchmark_parser.add_argument("--database", default="benchmark.db")
    benchmark_parser.add_argument("--output", default="reports/benchmark_report.json")
    benchmark_parser.set_defaults(func=command_benchmark)

    show_parser = subparsers.add_parser("show-ticket", help="show ticket details")
    show_parser.add_argument("--ticket-id", type=int, required=True)
    show_parser.add_argument("--database", default="ticket_agent.db")
    show_parser.set_defaults(func=command_show_ticket)

    health_parser = subparsers.add_parser("health", help="show runtime health")
    health_parser.add_argument("--database", default="ticket_agent.db")
    health_parser.set_defaults(func=command_health)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
