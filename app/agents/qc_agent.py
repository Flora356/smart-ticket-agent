from __future__ import annotations

from app.enums import FinalAction, RiskLevel, TicketPriority
from app.models.schemas import QCInput, QCOutput
from app.tools.risk_scanner import RiskScanner


class QCAgent:
    name = "qc_agent"

    def __init__(self, risk_scanner: RiskScanner) -> None:
        self.risk_scanner = risk_scanner

    def run(self, data: QCInput) -> QCOutput:
        issues: list[str] = []
        risk_flags = sorted(
            set(
                data.understand.risk_flags
                + data.process.need_human * ["process_need_human"]
                + data.respond.risk_flags
            )
        )
        scanned = self.risk_scanner.scan(data.respond.reply_draft)
        risk_flags = sorted(set(risk_flags + scanned.flags))

        if not data.respond.reply_draft.strip():
            issues.append("empty_reply")
        if not data.process.assigned_group:
            issues.append("missing_assigned_group")
        if not data.process.knowledge_hits and not data.process.need_human:
            issues.append("missing_knowledge_without_human")
        if data.process.need_human and data.understand.priority not in {
            TicketPriority.P0,
            TicketPriority.P1,
            TicketPriority.P2,
        }:
            issues.append("human_needed_but_priority_too_low")
        if any(flag.startswith("critical:") for flag in risk_flags):
            issues.append("critical_risk_detected")

        passed = not issues
        if any(flag.startswith("critical:") for flag in risk_flags):
            risk_level = RiskLevel.CRITICAL
        elif any(flag.startswith("high:") for flag in risk_flags):
            risk_level = RiskLevel.HIGH
        elif any(flag.startswith("medium:") for flag in risk_flags):
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        need_human = data.process.need_human or not passed or risk_level in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }

        if risk_level == RiskLevel.CRITICAL:
            final_action = FinalAction.HUMAN_REVIEW
        elif need_human:
            final_action = FinalAction.HUMAN_REVIEW
        elif passed:
            final_action = FinalAction.AUTO_REPLY
        else:
            final_action = FinalAction.RETRY

        confidence = min(
            0.99,
            max(
                0.0,
                (
                    data.understand.confidence
                    + data.process.retrieval_confidence
                    + data.respond.confidence
                )
                / 3,
            ),
        )

        return QCOutput(
            passed=passed,
            risk_level=risk_level,
            issues=issues,
            final_action=final_action,
            confidence=round(confidence, 4),
            need_human=need_human,
        )
