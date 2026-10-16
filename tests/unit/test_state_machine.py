from __future__ import annotations

import pytest

from app.enums import TicketStatus
from app.orchestrator.state_machine import InvalidTransition, TicketStateMachine


@pytest.mark.unit
def test_created_can_start_parsing() -> None:
    assert TicketStateMachine.can_transition(TicketStatus.CREATED, TicketStatus.PARSING)


@pytest.mark.unit
def test_created_cannot_jump_to_closed() -> None:
    assert not TicketStateMachine.can_transition(TicketStatus.CREATED, TicketStatus.CLOSED)


@pytest.mark.unit
def test_closed_is_terminal() -> None:
    assert TicketStateMachine.allowed_targets(TicketStatus.CLOSED) == set()


@pytest.mark.unit
def test_invalid_transition_raises() -> None:
    with pytest.raises(InvalidTransition):
        TicketStateMachine.assert_transition(TicketStatus.CLOSED, TicketStatus.DRAFTED)
