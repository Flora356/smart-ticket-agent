from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import (
    Difficulty,
    FinalAction,
    RiskLevel,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    TraceStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Ticket(StrictModel):
    id: int | None = None
    user_id: str = "anonymous"
    raw_content: str = Field(min_length=1)
    normalized_content: str | None = None
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus = TicketStatus.CREATED
    assigned_group: str | None = None
    assigned_to: str | None = None
    reply_draft: str | None = None
    final_action: FinalAction | None = None
    risk_level: RiskLevel | None = None
    trace_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TicketEvent(StrictModel):
    id: int | None = None
    ticket_id: int
    from_status: TicketStatus | None = None
    to_status: TicketStatus
    event_type: str
    operator: str = "orchestrator"
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AgentTrace(StrictModel):
    id: int | None = None
    ticket_id: int
    trace_id: str
    step_name: str
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] = Field(default_factory=dict)
    model_name: str = "local-rule-engine"
    prompt_version: str = "v1"
    token_input: int = 0
    token_output: int = 0
    latency_ms: int = 0
    status: TraceStatus = TraceStatus.SUCCESS
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class UnderstandOutput(StrictModel):
    normalized_question: str = Field(min_length=1)
    category: TicketCategory
    priority: TicketPriority
    confidence: float = Field(ge=0, le=1)
    need_human: bool = False
    keywords: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class ProcessOutput(StrictModel):
    knowledge_hits: list[str] = Field(default_factory=list)
    assigned_group: str = Field(min_length=1)
    route_reason: str = Field(min_length=1)
    need_human: bool = False
    retrieval_confidence: float = Field(default=0.0, ge=0, le=1)


class RespondOutput(StrictModel):
    reply_draft: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

    @field_validator("reply_draft")
    @classmethod
    def reject_empty_reply(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reply_draft cannot be blank")
        return value


class QCInput(StrictModel):
    ticket: Ticket
    understand: UnderstandOutput
    process: ProcessOutput
    respond: RespondOutput


class QCOutput(StrictModel):
    passed: bool
    risk_level: RiskLevel
    issues: list[str] = Field(default_factory=list)
    final_action: FinalAction
    confidence: float = Field(ge=0, le=1)
    need_human: bool = False


class BenchmarkItem(StrictModel):
    case_id: str
    difficulty: Difficulty
    category: str
    input_text: str
    expected_category: TicketCategory | None = None
    expected_priority: TicketPriority | None = None
    expected_group: str | None = None
    expected_status: TicketStatus | None = None
    expected_need_human: bool | None = None
    tags: list[str] = Field(default_factory=list)


class EvaluationResult(StrictModel):
    id: int | None = None
    case_id: str
    agent_name: str
    metric_name: str
    score: float = Field(ge=0, le=1)
    passed: bool
    reason: str = ""
    judge_model: str = "rule_based"
    created_at: datetime = Field(default_factory=utc_now)


class WorkflowRun(StrictModel):
    ticket: Ticket
    understood: UnderstandOutput
    processed: ProcessOutput
    responded: RespondOutput
    qc: QCOutput
    trace_id: str
    total_latency_ms: int = 0
