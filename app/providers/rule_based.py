from __future__ import annotations

from app.enums import TicketCategory, TicketPriority


class RuleBasedProvider:
    """Deterministic provider for local development, tests, and offline demos."""

    name = "rule_based"

    def __init__(self, model_name: str = "local-rule-engine") -> None:
        self.model_name = model_name

    def classify(
        self, text: str
    ) -> tuple[TicketCategory, TicketPriority, float, list[str]]:
        normalized = text.lower()

        category_scores: dict[TicketCategory, int] = {
            category: sum(1 for keyword in keywords if keyword in normalized)
            for category, keywords in [
                (
                    TicketCategory.ACCOUNT_SECURITY,
                    ["账号", "密码", "验证码", "被盗", "登录异常"],
                ),
                (TicketCategory.REFUND, ["退款", "退货", "退钱", "到账"]),
                (
                    TicketCategory.ORDER_AFTER_SALES,
                    ["订单", "发票", "物流", "发货", "售后"],
                ),
                (
                    TicketCategory.NETWORK_PAIRING,
                    [
                        "配网失败",
                        "配网",
                        "wifi",
                        "wi-fi",
                        "连不上",
                        "e104",
                        "联网",
                        "离线",
                        "掉线",
                    ],
                ),
                (
                    TicketCategory.DEVICE_FAULT,
                    [
                        "故障",
                        "无法开机",
                        "不开机",
                        "指示灯",
                        "出粮",
                        "卡粮",
                        "设备",
                        "猫砂盆",
                        "喂食器",
                        "传感器",
                        "滚筒",
                        "不自清洁",
                        "堵塞",
                        "异常",
                        "没电",
                    ],
                ),
                (TicketCategory.COMPLAINT, ["投诉", "态度", "差评", "曝光"]),
            ]
        }

        max_score = max(category_scores.values(), default=0)
        matched_category = TicketCategory.OTHER
        if max_score > 0:
            matched_category = next(
                category
                for category, score in category_scores.items()
                if score == max_score
            )
        matched_keywords = [
            keyword
            for category, keywords in [
                (
                    TicketCategory.ACCOUNT_SECURITY,
                    ["账号", "密码", "验证码", "被盗", "登录异常"],
                ),
                (TicketCategory.REFUND, ["退款", "退货", "退钱", "到账"]),
                (
                    TicketCategory.ORDER_AFTER_SALES,
                    ["订单", "发票", "物流", "发货", "售后"],
                ),
                (
                    TicketCategory.NETWORK_PAIRING,
                    ["配网失败", "配网", "wifi", "wi-fi", "连不上", "e104", "联网"],
                ),
                (
                    TicketCategory.DEVICE_FAULT,
                    ["故障", "无法开机", "指示灯", "出粮", "卡粮", "设备"],
                ),
                (TicketCategory.COMPLAINT, ["投诉", "态度", "差评", "曝光"]),
            ]
            if category == matched_category
            for keyword in keywords
            if keyword in normalized
        ]

        priority = TicketPriority.P3
        high_priority_keywords = ["起火", "漏电", "安全", "自燃", "伤到", "冒烟"]
        medium_priority_keywords = [
            "无法使用",
            "连不上",
            "配网失败",
            "配网",
            "退款",
            "投诉",
            "尽快",
            "紧急",
        ]
        if any(keyword in normalized for keyword in high_priority_keywords):
            priority = TicketPriority.P0
        elif matched_category in {
            TicketCategory.ACCOUNT_SECURITY,
            TicketCategory.REFUND,
            TicketCategory.COMPLAINT,
        }:
            priority = TicketPriority.P1
        elif any(keyword in normalized for keyword in medium_priority_keywords):
            priority = TicketPriority.P2

        confidence = 0.9 if matched_category != TicketCategory.OTHER else 0.45
        if matched_keywords:
            confidence = min(0.95, 0.7 + 0.05 * len(matched_keywords))

        return matched_category, priority, confidence, matched_keywords

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        if json_mode:
            return '{"message": "rule-based provider does not implement arbitrary JSON"}'
        return prompt
