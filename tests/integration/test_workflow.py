from __future__ import annotations

import pytest

from app.enums import FinalAction, TicketCategory, TicketPriority, TicketStatus


@pytest.mark.integration
def test_pairing_ticket_completes_full_workflow(container) -> None:
    result = container.workflow.run("AF205 配网失败，提示错误码 E104")
    assert result.ticket.status == TicketStatus.CLOSED
    assert result.ticket.category == TicketCategory.NETWORK_PAIRING
    assert result.ticket.priority == TicketPriority.P2
    assert result.ticket.assigned_group == "device_support"
    assert result.ticket.final_action == FinalAction.AUTO_REPLY
    assert result.respond.reply_draft


@pytest.mark.integration
def test_refund_ticket_routes_to_human(container) -> None:
    result = container.workflow.run("订单想退款，已经三天了还没到账")
    assert result.ticket.status == TicketStatus.NEED_HUMAN
    assert result.ticket.category == TicketCategory.REFUND
    assert result.ticket.assigned_group == "finance_after_sales"
    assert result.qc.need_human is True
    assert result.ticket.final_action == FinalAction.HUMAN_REVIEW


@pytest.mark.integration
def test_workflow_writes_trace_for_every_agent(container) -> None:
    result = container.workflow.run("AF203 喂食器卡粮了，请尽快处理")
    assert result.ticket.id is not None
    traces = container.repository.list_traces(result.ticket.id)
    step_names = {trace.step_name for trace in traces}
    assert {
        "understand_agent",
        "process_agent",
        "respond_agent",
        "qc_agent",
    }.issubset(step_names)


@pytest.mark.integration
def test_workflow_state_transitions_are_recorded(container) -> None:
    result = container.workflow.run("设备无法开机，指示灯不亮")
    assert result.ticket.id is not None
    events = container.repository.list_events(result.ticket.id)
    statuses = [event.to_status.value for event in events]
    assert statuses[0] == TicketStatus.PARSING.value
    assert TicketStatus.CLOSED.value in statuses


@pytest.mark.integration
def test_invalid_blank_ticket_is_rejected(container) -> None:
    with pytest.raises(Exception):
        container.workflow.run("   ")
