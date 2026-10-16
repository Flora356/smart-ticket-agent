from __future__ import annotations

from dataclasses import dataclass

from app.enums import TicketCategory, TicketPriority


@dataclass(frozen=True)
class RouteDecision:
    group: str
    reason: str
    need_human: bool


class TicketRouter:
    CATEGORY_GROUP = {
        TicketCategory.DEVICE_FAULT: "device_support",
        TicketCategory.NETWORK_PAIRING: "device_support",
        TicketCategory.ORDER_AFTER_SALES: "after_sales",
        TicketCategory.REFUND: "finance_after_sales",
        TicketCategory.ACCOUNT_SECURITY: "security_team",
        TicketCategory.COMPLAINT: "customer_success",
        TicketCategory.OTHER: "general_support",
    }

    HIGH_RISK_CATEGORIES = {
        TicketCategory.ACCOUNT_SECURITY,
        TicketCategory.REFUND,
        TicketCategory.COMPLAINT,
    }

    def route(
        self,
        category: TicketCategory,
        priority: TicketPriority,
        risk_flags: list[str] | None = None,
    ) -> RouteDecision:
        risk_flags = risk_flags or []
        group = self.CATEGORY_GROUP.get(category, "general_support")
        need_human = category in self.HIGH_RISK_CATEGORIES or priority in {
            TicketPriority.P0,
            TicketPriority.P1,
        }

        reasons = [f"category={category.value}", f"priority={priority.value}"]
        if risk_flags:
            reasons.append(f"risk_flags={','.join(sorted(risk_flags))}")
        if need_human:
            reasons.append("high_risk_or_high_priority")

        return RouteDecision(
            group=group,
            reason="; ".join(reasons),
            need_human=need_human,
        )
