from __future__ import annotations

import pytest

from app.enums import TicketStatus
from app.models.schemas import AgentTrace, Ticket, TicketEvent


@pytest.mark.integration
def test_create_and_update_ticket(container) -> None:
    ticket = container.repository.create_ticket(Ticket(raw_content="设备无法联网"))
    assert ticket.id is not None
    assert ticket.status == TicketStatus.CREATED

    updated = container.repository.save_ticket(
        ticket.model_copy(update={"status": TicketStatus.PARSING})
    )
    assert updated.status == TicketStatus.PARSING


@pytest.mark.integration
def test_append_and_read_events(container) -> None:
    ticket = container.repository.create_ticket(Ticket(raw_content="退款没到账"))
    assert ticket.id is not None
    container.repository.append_event(
        TicketEvent(
            ticket_id=ticket.id,
            from_status=TicketStatus.CREATED,
            to_status=TicketStatus.PARSING,
            event_type="start",
        )
    )
    events = container.repository.list_events(ticket.id)
    assert len(events) == 1
    assert events[0].to_status == TicketStatus.PARSING


@pytest.mark.integration
def test_trace_unique_step_constraint(container) -> None:
    ticket = container.repository.create_ticket(Ticket(raw_content="设备故障"))
    assert ticket.id is not None
    trace = AgentTrace(
        ticket_id=ticket.id,
        trace_id="trace-1",
        step_name="understand_agent",
        input_json={"text": "设备故障"},
        output_json={"category": "device_fault"},
    )
    container.repository.append_trace(trace)
    with pytest.raises(Exception):
        container.repository.append_trace(trace)
