from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import CreateTicketRequest, DecisionRequest
from app.config import AppConfig, PROJECT_ROOT
from app.container import ApplicationContainer
from app.enums import FinalAction, TicketStatus
from app.models.schemas import Ticket, TicketEvent


def _build_container() -> ApplicationContainer:
    config = AppConfig.from_env()
    return ApplicationContainer(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = _build_container()
    try:
        yield
    finally:
        app.state.container.close()


app = FastAPI(
    title="Smart Ticket Agent API",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_container() -> ApplicationContainer:
    return app.state.container


ContainerDep = Annotated[ApplicationContainer, Depends(get_container)]


@app.get("/api/health")
def health(container: ContainerDep) -> dict:
    return {
        "status": "ok",
        "provider": container.provider.name,
        "model": container.provider.model_name,
        "database": str(container.repository.database_path),
        "status_counts": container.repository.status_counts(),
    }


@app.post("/api/tickets")
def create_ticket(request: CreateTicketRequest, container: ContainerDep) -> dict:
    result = container.workflow.run(request.text, user_id=request.user_id)
    return _ticket_detail(container, result.ticket.id, result=result)


@app.get("/api/tickets")
def list_tickets(container: ContainerDep, limit: int = 50) -> dict:
    tickets = container.repository.list_tickets(limit=limit)
    return {"items": [_ticket_summary(ticket) for ticket in tickets]}


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int, container: ContainerDep) -> dict:
    detail = _ticket_detail(container, ticket_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return detail


@app.post("/api/tickets/{ticket_id}/decision")
def decide_ticket(
    ticket_id: int,
    request: DecisionRequest,
    container: ContainerDep,
) -> dict:
    ticket = container.repository.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    if ticket.status != TicketStatus.NEED_HUMAN:
        raise HTTPException(
            status_code=409,
            detail=f"ticket is {ticket.status.value}, not NEED_HUMAN",
        )

    if request.decision == "close":
        target = TicketStatus.CLOSED
        final_action = FinalAction.AUTO_CLOSE
        event_type = "human_closed"
    elif request.decision == "reject":
        target = TicketStatus.CLOSED
        final_action = FinalAction.REJECT
        event_type = "human_rejected"
    else:
        target = TicketStatus.CLOSED
        final_action = FinalAction.AUTO_REPLY
        event_type = "human_approved"

    container.repository.append_event(
        TicketEvent(
            ticket_id=ticket.id or ticket_id,
            from_status=ticket.status,
            to_status=target,
            event_type=event_type,
            operator=request.operator,
            payload={"note": request.note},
        )
    )
    updated = container.repository.save_ticket(
        ticket.model_copy(
            update={
                "status": target,
                "final_action": final_action,
            }
        )
    )
    return _ticket_detail(container, updated.id)


@app.get("/api/benchmark")
def benchmark_summary(container: ContainerDep) -> dict:
    report_path = PROJECT_ROOT / "reports" / "benchmark_report.json"
    if not report_path.exists():
        return {"available": False, "message": "run benchmark first"}

    import json

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return {"available": True, **payload}


def _ticket_summary(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "raw_content": ticket.raw_content,
        "category": ticket.category.value if ticket.category else None,
        "priority": ticket.priority.value if ticket.priority else None,
        "status": ticket.status.value,
        "assigned_group": ticket.assigned_group,
        "final_action": ticket.final_action.value if ticket.final_action else None,
        "risk_level": ticket.risk_level.value if ticket.risk_level else None,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }


def _ticket_detail(container: ApplicationContainer, ticket_id: int | None, result=None) -> dict | None:
    if ticket_id is None:
        return None
    ticket = container.repository.get_ticket(ticket_id)
    if ticket is None:
        return None

    events = container.repository.list_events(ticket_id)
    traces = container.repository.list_traces(ticket_id)
    payload = {
        "ticket": _ticket_summary(ticket),
        "content": {
            "raw": ticket.raw_content,
            "normalized": ticket.normalized_content,
            "reply_draft": ticket.reply_draft,
        },
        "events": [
            {
                "id": event.id,
                "from_status": event.from_status.value if event.from_status else None,
                "to_status": event.to_status.value,
                "event_type": event.event_type,
                "operator": event.operator,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
        "traces": [
            {
                "id": trace.id,
                "step_name": trace.step_name,
                "status": trace.status.value,
                "latency_ms": trace.latency_ms,
                "input": trace.input_json,
                "output": trace.output_json,
                "created_at": trace.created_at.isoformat(),
            }
            for trace in traces
        ],
        "cost_units": container.repository.total_cost_units(ticket_id),
    }
    if result is not None:
        payload["analysis"] = {
            "understood": result.understand.model_dump(mode="json"),
            "processed": result.process.model_dump(mode="json"),
            "responded": result.respond.model_dump(mode="json"),
            "qc": result.qc.model_dump(mode="json"),
        }
    else:
        payload["analysis"] = _analysis_from_traces(traces)
    return payload


def _analysis_from_traces(traces: list) -> dict:
    analysis: dict[str, dict] = {}
    mapping = {
        "understand_agent": "understood",
        "process_agent": "processed",
        "respond_agent": "responded",
        "qc_agent": "qc",
    }
    for trace in traces:
        key = mapping.get(trace.step_name)
        if key:
            analysis[key] = trace.output_json
    return analysis
