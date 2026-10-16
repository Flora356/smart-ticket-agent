from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from app.agents.process_agent import ProcessAgent
from app.agents.qc_agent import QCAgent
from app.agents.respond_agent import RespondAgent
from app.agents.understand_agent import UnderstandAgent
from app.enums import FinalAction, TicketStatus, TraceStatus
from app.models.schemas import (
    AgentTrace,
    ProcessOutput,
    QCInput,
    QCOutput,
    RespondOutput,
    Ticket,
    TicketEvent,
    UnderstandOutput,
)
from app.orchestrator.state_machine import TicketStateMachine
from app.storage.sqlite_repository import SQLiteTicketRepository


@dataclass
class WorkflowResult:
    ticket: Ticket
    understand: UnderstandOutput
    process: ProcessOutput
    respond: RespondOutput
    qc: QCOutput
    trace_id: str
    total_latency_ms: int


class TicketWorkflow:
    def __init__(
        self,
        repository: SQLiteTicketRepository,
        understand_agent: UnderstandAgent,
        process_agent: ProcessAgent,
        respond_agent: RespondAgent,
        qc_agent: QCAgent,
        *,
        max_retries: int = 2,
        auto_reply_enabled: bool = True,
        model_name: str = "local-rule-engine",
    ) -> None:
        self.repository = repository
        self.understand_agent = understand_agent
        self.process_agent = process_agent
        self.respond_agent = respond_agent
        self.qc_agent = qc_agent
        self.max_retries = max_retries
        self.auto_reply_enabled = auto_reply_enabled
        self.model_name = model_name

    def run(self, raw_content: str, user_id: str = "anonymous") -> WorkflowResult:
        trace_id = uuid4().hex
        started = perf_counter()
        ticket = self.repository.create_ticket(
            Ticket(
                user_id=user_id,
                raw_content=raw_content,
                trace_id=trace_id,
            )
        )
        if ticket.id is None:
            raise RuntimeError("created ticket has no id")

        self._append_event(ticket, TicketStatus.PARSING, "workflow_started")
        ticket = self._transition(ticket, TicketStatus.PARSING, "start_parsing")

        try:
            understand = self._run_understand(ticket, raw_content, trace_id)
            ticket = self._apply_understand(ticket, understand)

            process = self._run_process(ticket, understand, trace_id)
            ticket = self._apply_process(ticket, process)

            respond = self._run_respond(ticket, understand, process, trace_id)
            ticket = self._apply_respond(ticket, respond)

            qc = self._run_qc(ticket, understand, process, respond, trace_id)
            ticket = self._apply_qc(ticket, qc)
        except Exception as exc:
            ticket = self._transition(
                ticket,
                TicketStatus.FAILED,
                "workflow_failed",
                payload={"error": str(exc)},
            )
            self._record_trace(
                ticket,
                trace_id,
                "workflow",
                {"raw_content": raw_content},
                {"error": str(exc)},
                0,
                TraceStatus.FAILED,
                str(exc),
            )
            raise

        total_latency_ms = max(0, int((perf_counter() - started) * 1000))
        refreshed = self.repository.get_ticket(ticket.id)
        if refreshed is None:
            raise RuntimeError(f"ticket {ticket.id} disappeared")
        return WorkflowResult(
            ticket=refreshed,
            understand=understand,
            process=process,
            respond=respond,
            qc=qc,
            trace_id=trace_id,
            total_latency_ms=total_latency_ms,
        )

    def _run_understand(
        self, ticket: Ticket, raw_content: str, trace_id: str
    ) -> UnderstandOutput:
        started = perf_counter()
        output = self.understand_agent.run(raw_content)
        self._record_trace(
            ticket,
            trace_id,
            "understand_agent",
            {"raw_content": raw_content},
            output.model_dump(mode="json"),
            int((perf_counter() - started) * 1000),
        )
        return output

    def _run_process(
        self,
        ticket: Ticket,
        understood: UnderstandOutput,
        trace_id: str,
    ) -> ProcessOutput:
        started = perf_counter()
        output = self.process_agent.run(understood.normalized_question, understood)
        self._record_trace(
            ticket,
            trace_id,
            "process_agent",
            understood.model_dump(mode="json"),
            output.model_dump(mode="json"),
            int((perf_counter() - started) * 1000),
        )
        return output

    def _run_respond(
        self,
        ticket: Ticket,
        understood: UnderstandOutput,
        processed: ProcessOutput,
        trace_id: str,
    ) -> RespondOutput:
        started = perf_counter()
        output = self.respond_agent.run(
            understood.normalized_question,
            understood,
            processed,
        )
        self._record_trace(
            ticket,
            trace_id,
            "respond_agent",
            {
                "understand": understood.model_dump(mode="json"),
                "process": processed.model_dump(mode="json"),
            },
            output.model_dump(mode="json"),
            int((perf_counter() - started) * 1000),
        )
        return output

    def _run_qc(
        self,
        ticket: Ticket,
        understood: UnderstandOutput,
        processed: ProcessOutput,
        responded: RespondOutput,
        trace_id: str,
    ) -> QCOutput:
        started = perf_counter()
        output = self.qc_agent.run(
            QCInput(
                ticket=ticket,
                understand=understood,
                process=processed,
                respond=responded,
            )
        )
        self._record_trace(
            ticket,
            trace_id,
            "qc_agent",
            {
                "understand": understood.model_dump(mode="json"),
                "process": processed.model_dump(mode="json"),
                "respond": responded.model_dump(mode="json"),
            },
            output.model_dump(mode="json"),
            int((perf_counter() - started) * 1000),
        )
        return output

    def _apply_understand(
        self, ticket: Ticket, understood: UnderstandOutput
    ) -> Ticket:
        ticket = ticket.model_copy(
            update={
                "normalized_content": understood.normalized_question,
                "category": understood.category,
                "priority": understood.priority,
                "risk_level": None,
            }
        )
        ticket = self._transition(ticket, TicketStatus.PARSED, "understand_completed")
        return self.repository.save_ticket(ticket)

    def _apply_process(self, ticket: Ticket, processed: ProcessOutput) -> Ticket:
        ticket = ticket.model_copy(
            update={
                "assigned_group": processed.assigned_group,
            }
        )
        ticket = self._transition(ticket, TicketStatus.PROCESSING, "process_started")
        ticket = self._transition(ticket, TicketStatus.DRAFTED, "process_completed")
        return self.repository.save_ticket(ticket)

    def _apply_respond(self, ticket: Ticket, responded: RespondOutput) -> Ticket:
        ticket = ticket.model_copy(update={"reply_draft": responded.reply_draft})
        ticket = self._transition(ticket, TicketStatus.REVIEWING, "respond_completed")
        return self.repository.save_ticket(ticket)

    def _apply_qc(self, ticket: Ticket, qc: QCOutput) -> Ticket:
        if qc.final_action == FinalAction.REJECT:
            target = TicketStatus.REJECTED
        elif qc.need_human and not self.auto_reply_enabled:
            target = TicketStatus.NEED_HUMAN
        elif qc.need_human:
            target = TicketStatus.NEED_HUMAN
        elif qc.passed:
            target = TicketStatus.APPROVED
        else:
            target = TicketStatus.RETRYING

        ticket = self._transition(ticket, target, "qc_completed", payload=qc.model_dump(mode="json"))
        ticket = ticket.model_copy(
            update={
                "final_action": qc.final_action,
                "risk_level": qc.risk_level,
            }
        )
        ticket = self.repository.save_ticket(ticket)

        if target == TicketStatus.APPROVED:
            ticket = self._transition(ticket, TicketStatus.REPLIED, "reply_sent")
            ticket = self.repository.save_ticket(ticket)
            ticket = self._transition(ticket, TicketStatus.CLOSED, "ticket_closed")
            ticket = self.repository.save_ticket(ticket)
        return ticket

    def _transition(
        self,
        ticket: Ticket,
        target: TicketStatus,
        event_type: str,
        *,
        payload: dict | None = None,
    ) -> Ticket:
        current = ticket.status
        TicketStateMachine.assert_transition(current, target)
        self._append_event(ticket, target, event_type, payload=payload, from_status=current)
        updated = ticket.model_copy(update={"status": target})
        return self.repository.save_ticket(updated)

    def _append_event(
        self,
        ticket: Ticket,
        target: TicketStatus,
        event_type: str,
        *,
        payload: dict | None = None,
        from_status: TicketStatus | None = None,
    ) -> None:
        if ticket.id is None:
            raise RuntimeError("cannot append event for unsaved ticket")
        self.repository.append_event(
            TicketEvent(
                ticket_id=ticket.id,
                from_status=from_status,
                to_status=target,
                event_type=event_type,
                payload=payload or {},
            )
        )

    def _record_trace(
        self,
        ticket: Ticket,
        trace_id: str,
        step_name: str,
        input_json: dict,
        output_json: dict,
        latency_ms: int,
        status: TraceStatus = TraceStatus.SUCCESS,
        error_message: str | None = None,
    ) -> None:
        if ticket.id is None:
            raise RuntimeError("cannot trace unsaved ticket")
        self.repository.append_trace(
            AgentTrace(
                ticket_id=ticket.id,
                trace_id=trace_id,
                step_name=step_name,
                input_json=input_json,
                output_json=output_json,
                model_name=self.model_name,
                token_input=0,
                token_output=0,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
            )
        )
