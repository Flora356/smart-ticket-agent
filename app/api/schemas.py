from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTicketRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: str = "web-user"


class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|close|reject)$")
    operator: str = "human-agent"
    note: str = ""
