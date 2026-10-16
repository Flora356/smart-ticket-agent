from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.enums import TicketStatus
from app.models.schemas import AgentTrace, EvaluationResult, Ticket, TicketEvent


def _serialize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


class SQLiteTicketRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self.initialize()

    def close(self) -> None:
        self._connection.close()

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                normalized_content TEXT,
                category TEXT,
                priority TEXT,
                status TEXT NOT NULL,
                assigned_group TEXT,
                assigned_to TEXT,
                reply_draft TEXT,
                final_action TEXT,
                risk_level TEXT,
                trace_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ticket_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                event_type TEXT NOT NULL,
                operator TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
            );

            CREATE TABLE IF NOT EXISTS agent_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                trace_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                token_input INTEGER NOT NULL,
                token_output INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
            );

            CREATE TABLE IF NOT EXISTS eval_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                score REAL NOT NULL,
                passed INTEGER NOT NULL,
                reason TEXT NOT NULL,
                judge_model TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket
                ON ticket_events(ticket_id, id);
            CREATE INDEX IF NOT EXISTS idx_agent_traces_ticket
                ON agent_traces(ticket_id, id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_traces_unique_step
                ON agent_traces(ticket_id, trace_id, step_name);
            """
        )
        self._connection.commit()

    def create_ticket(self, ticket: Ticket) -> Ticket:
        cursor = self._connection.execute(
            """
            INSERT INTO tickets (
                user_id, raw_content, normalized_content, category, priority, status,
                assigned_group, assigned_to, reply_draft, final_action, risk_level,
                trace_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.user_id,
                ticket.raw_content,
                ticket.normalized_content,
                ticket.category.value if ticket.category else None,
                ticket.priority.value if ticket.priority else None,
                ticket.status.value,
                ticket.assigned_group,
                ticket.assigned_to,
                ticket.reply_draft,
                ticket.final_action.value if ticket.final_action else None,
                ticket.risk_level.value if ticket.risk_level else None,
                ticket.trace_id,
                _serialize_datetime(ticket.created_at),
                _serialize_datetime(ticket.updated_at),
            ),
        )
        self._connection.commit()
        ticket_id = int(cursor.lastrowid)
        created = self.get_ticket(ticket_id)
        if created is None:
            raise RuntimeError("ticket insert succeeded but row was not found")
        return created

    def save_ticket(self, ticket: Ticket) -> Ticket:
        if ticket.id is None:
            return self.create_ticket(ticket)
        self._connection.execute(
            """
            UPDATE tickets SET
                user_id = ?,
                raw_content = ?,
                normalized_content = ?,
                category = ?,
                priority = ?,
                status = ?,
                assigned_group = ?,
                assigned_to = ?,
                reply_draft = ?,
                final_action = ?,
                risk_level = ?,
                trace_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                ticket.user_id,
                ticket.raw_content,
                ticket.normalized_content,
                ticket.category.value if ticket.category else None,
                ticket.priority.value if ticket.priority else None,
                ticket.status.value,
                ticket.assigned_group,
                ticket.assigned_to,
                ticket.reply_draft,
                ticket.final_action.value if ticket.final_action else None,
                ticket.risk_level.value if ticket.risk_level else None,
                ticket.trace_id,
                _serialize_datetime(ticket.updated_at),
                ticket.id,
            ),
        )
        self._connection.commit()
        updated = self.get_ticket(ticket.id)
        if updated is None:
            raise RuntimeError(f"ticket {ticket.id} was not found after update")
        return updated

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        row = self._connection.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        return self._row_to_ticket(row) if row else None

    def list_tickets(self, limit: int = 20) -> list[Ticket]:
        rows = self._connection.execute(
            "SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_ticket(row) for row in rows]

    def append_event(self, event: TicketEvent) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO ticket_events (
                ticket_id, from_status, to_status, event_type, operator,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.ticket_id,
                event.from_status.value if event.from_status else None,
                event.to_status.value,
                event.event_type,
                event.operator,
                json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                _serialize_datetime(event.created_at),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def list_events(self, ticket_id: int) -> list[TicketEvent]:
        rows = self._connection.execute(
            "SELECT * FROM ticket_events WHERE ticket_id = ? ORDER BY id",
            (ticket_id,),
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def append_trace(self, trace: AgentTrace) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO agent_traces (
                ticket_id, trace_id, step_name, input_json, output_json,
                model_name, prompt_version, token_input, token_output,
                latency_ms, status, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace.ticket_id,
                trace.trace_id,
                trace.step_name,
                json.dumps(trace.input_json, ensure_ascii=False, sort_keys=True),
                json.dumps(trace.output_json, ensure_ascii=False, sort_keys=True),
                trace.model_name,
                trace.prompt_version,
                trace.token_input,
                trace.token_output,
                trace.latency_ms,
                trace.status.value,
                trace.error_message,
                _serialize_datetime(trace.created_at),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def list_traces(self, ticket_id: int) -> list[AgentTrace]:
        rows = self._connection.execute(
            "SELECT * FROM agent_traces WHERE ticket_id = ? ORDER BY id",
            (ticket_id,),
        ).fetchall()
        return [self._row_to_trace(row) for row in rows]

    def total_cost_units(self, ticket_id: int) -> int:
        row = self._connection.execute(
            """
            SELECT COALESCE(SUM(token_input + token_output), 0) AS total
            FROM agent_traces WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()
        return int(row["total"])

    def append_eval_result(self, result: EvaluationResult) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO eval_results (
                case_id, agent_name, metric_name, score, passed, reason,
                judge_model, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.case_id,
                result.agent_name,
                result.metric_name,
                result.score,
                int(result.passed),
                result.reason,
                result.judge_model,
                _serialize_datetime(result.created_at),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def list_eval_results(self, case_id: str | None = None) -> list[EvaluationResult]:
        if case_id:
            rows = self._connection.execute(
                "SELECT * FROM eval_results WHERE case_id = ? ORDER BY id",
                (case_id,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT * FROM eval_results ORDER BY id"
            ).fetchall()
        return [
            EvaluationResult(
                id=row["id"],
                case_id=row["case_id"],
                agent_name=row["agent_name"],
                metric_name=row["metric_name"],
                score=row["score"],
                passed=bool(row["passed"]),
                reason=row["reason"],
                judge_model=row["judge_model"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def status_counts(self) -> dict[str, int]:
        rows = self._connection.execute(
            "SELECT status, COUNT(*) AS count FROM tickets GROUP BY status"
        ).fetchall()
        return {row["status"]: int(row["count"]) for row in rows}

    @staticmethod
    def _row_to_ticket(row: sqlite3.Row) -> Ticket:
        from app.enums import FinalAction, RiskLevel, TicketCategory, TicketPriority

        return Ticket(
            id=row["id"],
            user_id=row["user_id"],
            raw_content=row["raw_content"],
            normalized_content=row["normalized_content"],
            category=TicketCategory(row["category"]) if row["category"] else None,
            priority=TicketPriority(row["priority"]) if row["priority"] else None,
            status=TicketStatus(row["status"]),
            assigned_group=row["assigned_group"],
            assigned_to=row["assigned_to"],
            reply_draft=row["reply_draft"],
            final_action=FinalAction(row["final_action"]) if row["final_action"] else None,
            risk_level=RiskLevel(row["risk_level"]) if row["risk_level"] else None,
            trace_id=row["trace_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> TicketEvent:
        return TicketEvent(
            id=row["id"],
            ticket_id=row["ticket_id"],
            from_status=TicketStatus(row["from_status"]) if row["from_status"] else None,
            to_status=TicketStatus(row["to_status"]),
            event_type=row["event_type"],
            operator=row["operator"],
            payload=json.loads(row["payload_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _row_to_trace(row: sqlite3.Row) -> AgentTrace:
        from app.enums import TraceStatus

        return AgentTrace(
            id=row["id"],
            ticket_id=row["ticket_id"],
            trace_id=row["trace_id"],
            step_name=row["step_name"],
            input_json=json.loads(row["input_json"]),
            output_json=json.loads(row["output_json"]),
            model_name=row["model_name"],
            prompt_version=row["prompt_version"],
            token_input=row["token_input"],
            token_output=row["token_output"],
            latency_ms=row["latency_ms"],
            status=TraceStatus(row["status"]),
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
