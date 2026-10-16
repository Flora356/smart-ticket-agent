from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.enums import TicketCategory, TicketPriority
from app.models.schemas import UnderstandOutput


@pytest.mark.unit
def test_understand_schema_accepts_valid_payload() -> None:
    result = UnderstandOutput(
        normalized_question="设备卡粮",
        category=TicketCategory.DEVICE_FAULT,
        priority=TicketPriority.P2,
        confidence=0.8,
    )
    assert result.category == TicketCategory.DEVICE_FAULT


@pytest.mark.unit
def test_understand_schema_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        UnderstandOutput(
            normalized_question="设备卡粮",
            category=TicketCategory.DEVICE_FAULT,
            priority=TicketPriority.P2,
            confidence=0.8,
            unexpected=True,
        )


@pytest.mark.unit
def test_understand_schema_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError):
        UnderstandOutput(
            normalized_question="设备卡粮",
            category=TicketCategory.DEVICE_FAULT,
            priority=TicketPriority.P2,
            confidence=1.1,
        )
