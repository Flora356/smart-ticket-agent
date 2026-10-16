from __future__ import annotations

from enum import StrEnum


class TicketStatus(StrEnum):
    CREATED = "CREATED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    PROCESSING = "PROCESSING"
    DRAFTED = "DRAFTED"
    REVIEWING = "REVIEWING"
    APPROVED = "APPROVED"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"
    NEED_HUMAN = "NEED_HUMAN"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    REJECTED = "REJECTED"


class TicketCategory(StrEnum):
    DEVICE_FAULT = "device_fault"
    NETWORK_PAIRING = "network_pairing"
    ORDER_AFTER_SALES = "order_after_sales"
    REFUND = "refund"
    ACCOUNT_SECURITY = "account_security"
    COMPLAINT = "complaint"
    OTHER = "other"


class TicketPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FinalAction(StrEnum):
    AUTO_REPLY = "auto_reply"
    HUMAN_REVIEW = "human_review"
    RETRY = "retry"
    REJECT = "reject"
    AUTO_CLOSE = "auto_close"


class TraceStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Difficulty(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
