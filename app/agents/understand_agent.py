from __future__ import annotations

from app.enums import TicketPriority
from app.models.schemas import UnderstandOutput
from app.providers.rule_based import RuleBasedProvider
from app.tools.risk_scanner import RiskScanner


class UnderstandAgent:
    name = "understand_agent"

    def __init__(
        self,
        provider: RuleBasedProvider,
        risk_scanner: RiskScanner,
        confidence_threshold: float,
    ) -> None:
        self.provider = provider
        self.risk_scanner = risk_scanner
        self.confidence_threshold = confidence_threshold

    def run(self, text: str) -> UnderstandOutput:
        category, priority, confidence, keywords = self.provider.classify(text)
        risk = self.risk_scanner.scan(text)

        if risk.has_high_risk:
            priority = (
                TicketPriority.P0
                if any(flag.startswith("critical:") for flag in risk.flags)
                else TicketPriority.P1
            )

        need_human = (
            confidence < self.confidence_threshold
            or risk.has_high_risk
            or priority in {TicketPriority.P0, TicketPriority.P1}
        )

        return UnderstandOutput(
            normalized_question=" ".join(text.strip().split()),
            category=category,
            priority=priority,
            confidence=confidence,
            need_human=need_human,
            keywords=keywords,
            risk_flags=risk.flags,
        )
