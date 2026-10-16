from __future__ import annotations

from app.enums import TicketStatus


class InvalidTransition(ValueError):
    pass


class TicketStateMachine:
    """Explicit state machine for ticket lifecycle."""

    TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
        TicketStatus.CREATED: {TicketStatus.PARSING, TicketStatus.FAILED},
        TicketStatus.PARSING: {TicketStatus.PARSED, TicketStatus.RETRYING, TicketStatus.FAILED},
        TicketStatus.PARSED: {TicketStatus.PROCESSING, TicketStatus.FAILED},
        TicketStatus.PROCESSING: {
            TicketStatus.DRAFTED,
            TicketStatus.RETRYING,
            TicketStatus.FAILED,
        },
        TicketStatus.DRAFTED: {TicketStatus.REVIEWING, TicketStatus.FAILED},
        TicketStatus.REVIEWING: {
            TicketStatus.APPROVED,
            TicketStatus.NEED_HUMAN,
            TicketStatus.REJECTED,
            TicketStatus.RETRYING,
            TicketStatus.FAILED,
        },
        TicketStatus.APPROVED: {TicketStatus.REPLIED, TicketStatus.NEED_HUMAN},
        TicketStatus.REPLIED: {TicketStatus.CLOSED},
        TicketStatus.RETRYING: {
            TicketStatus.PARSING,
            TicketStatus.PROCESSING,
            TicketStatus.REVIEWING,
        },
        TicketStatus.NEED_HUMAN: {TicketStatus.CLOSED},
        TicketStatus.REJECTED: {TicketStatus.NEED_HUMAN, TicketStatus.CLOSED},
        TicketStatus.FAILED: {TicketStatus.RETRYING, TicketStatus.NEED_HUMAN},
        TicketStatus.CLOSED: set(),
    }

    @classmethod
    def can_transition(cls, current: TicketStatus, target: TicketStatus) -> bool:
        if current == target:
            return True
        return target in cls.TRANSITIONS.get(current, set())

    @classmethod
    def assert_transition(cls, current: TicketStatus, target: TicketStatus) -> None:
        if not cls.can_transition(current, target):
            raise InvalidTransition(
                f"invalid ticket transition: {current.value} -> {target.value}"
            )

    @classmethod
    def allowed_targets(cls, current: TicketStatus) -> set[TicketStatus]:
        return set(cls.TRANSITIONS.get(current, set()))
