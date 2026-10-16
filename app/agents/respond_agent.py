from __future__ import annotations

from app.enums import TicketCategory
from app.models.schemas import ProcessOutput, RespondOutput, UnderstandOutput
from app.tools.risk_scanner import RiskScanner


class RespondAgent:
    name = "respond_agent"

    # Safety-critical phrasings. These must never invite the user to
    # self-troubleshoot a possibly dangerous device.
    SAFETY_KEYWORDS = (
        "漏电",
        "触电",
        "麻手",
        "发烫",
        "过热",
        "烫手",
        "烧焦",
        "焦味",
        "糊味",
        "冒烟",
        "起火",
        "自燃",
        "电源线破损",
        "电线破损",
    )

    SAFETY_OPENER = (
        "这个问题涉及人身安全，请优先处理下面的安全事项，不要尝试自行拆机排查："
    )
    SAFETY_CLOSER = (
        "安全第一，我们已将这条工单升级为最高优先级，专项团队会尽快与您联系安排好检测与换机。"
    )

    OPENERS = {
        TicketCategory.NETWORK_PAIRING: "设备联网问题通常和 Wi-Fi 频段或配网状态有关，可以按下面几步排查：",
        TicketCategory.DEVICE_FAULT: "这类设备异常大多可以现场排查，建议按顺序试一下：",
        TicketCategory.ORDER_AFTER_SALES: "关于订单和物流，处理方式如下：",
        TicketCategory.REFUND: "关于退款，规则和处理进度如下：",
        TicketCategory.ACCOUNT_SECURITY: "账号安全是最高优先级，请先按下面的方式保护自己：",
        TicketCategory.COMPLAINT: "非常抱歉给您带来不好的体验，我们会这样处理：",
    }

    CLOSERS = {
        TicketCategory.NETWORK_PAIRING: "如果按上面操作还是连不上，请把路由器型号、设备指示灯状态和报错截图发我们，会安排工程师继续跟进。",
        TicketCategory.DEVICE_FAULT: "如果排查后仍不正常，请提供设备型号、SN 和一段故障视频，我们判断是否需要走售后。",
        TicketCategory.ORDER_AFTER_SALES: "如果需要加急，把订单号发我，我帮您标记优先处理。",
        TicketCategory.REFUND: "如对退款进度有疑问，请提供订单号，我帮您查询当前卡在哪一步。",
        TicketCategory.ACCOUNT_SECURITY: "请放心，我们不会向任何人索要您的密码或验证码，这条工单已转交安全团队。",
        TicketCategory.COMPLAINT: "您的反馈已完整记录，主管会在 24 小时内回访处理进展。",
    }

    def __init__(self, risk_scanner: RiskScanner) -> None:
        self.risk_scanner = risk_scanner

    def run(
        self,
        question: str,
        understood: UnderstandOutput,
        processed: ProcessOutput,
    ) -> RespondOutput:
        citations = [hit.split(":", 1)[0] for hit in processed.knowledge_hits]

        if processed.knowledge_hits:
            draft = self._compose(understood, processed)
            confidence = min(0.94, 0.6 + processed.retrieval_confidence)
        elif processed.need_human:
            draft = (
                "您好，您反馈的问题涉及风险或需要人工核验，已转交对应支持团队优先处理。"
                "请保留设备 SN、订单号或相关截图，工作人员会尽快与您联系。"
            )
            confidence = 0.75
        else:
            draft = (
                "您好，您描述的情况暂时没有完全对应的处理方案，我先帮您记录并转交人工支持。"
                "为了让同事更快定位，麻烦补充：设备型号、SN、错误码，或者订单号与截图。"
            )
            confidence = 0.5

        risk = self.risk_scanner.scan(draft)
        return RespondOutput(
            reply_draft=draft,
            citations=citations,
            risk_flags=sorted(set(understood.risk_flags + risk.flags)),
            confidence=confidence,
        )

    def _compose(self, understood: UnderstandOutput, processed: ProcessOutput) -> str:
        """Build a natural reply from the retrieved knowledge chunks."""
        category = understood.category
        steps = self._extract_steps(processed.knowledge_hits)
        is_safety = self._is_safety_issue(understood, processed)

        if is_safety:
            opener = self.SAFETY_OPENER
        else:
            opener = self.OPENERS.get(category, "您好，根据您的问题，处理建议如下：")

        question = understood.normalized_question
        if len(question) > 40:
            question = question[:40] + "…"

        parts = [f"您好，关于「{question}」。", opener]
        parts.extend(steps)

        if processed.need_human:
            parts.append("另外，这条工单因涉及风险或需要人工核验，已同步转交专项支持团队。")

        if is_safety:
            parts.append(self.SAFETY_CLOSER)
        else:
            parts.append(
                self.CLOSERS.get(category, "如仍有问题请继续回复本工单，我们会跟进。")
            )
        return "".join(parts)

    def _is_safety_issue(
        self, understood: UnderstandOutput, processed: ProcessOutput
    ) -> bool:
        """Detect safety-critical tickets regardless of retrieval luck."""
        haystack = " ".join(
            [
                understood.normalized_question,
                " ".join(understood.keywords),
                " ".join(understood.risk_flags),
                " ".join(processed.knowledge_hits),
            ]
        ).lower()
        if any(keyword in haystack for keyword in self.SAFETY_KEYWORDS):
            return True
        return any(
            flag.startswith("critical:safety_hazard") for flag in understood.risk_flags
        )

    @staticmethod
    def _extract_steps(knowledge_hits: list[str]) -> list[str]:
        """Pull the top knowledge chunk's numbered steps into separate lines."""
        if not knowledge_hits:
            return []

        body = knowledge_hits[0].split(": ", 1)[-1].strip()
        normalized = body.replace("；", ";")
        raw_steps = [step.strip() for step in normalized.split(";") if step.strip()]
        if not raw_steps:
            return [body]

        rendered: list[str] = []
        for index, step in enumerate(raw_steps[:5], start=1):
            cleaned = _strip_step_prefix(step)
            cleaned = cleaned.strip("；;。 ")
            if not cleaned:
                continue
            rendered.append(f"{index}. {cleaned}；")
        return rendered


_STEP_PREFIXES = (
    "1)",
    "2)",
    "3)",
    "4)",
    "5)",
    "1、",
    "2、",
    "3、",
    "4、",
    "5、",
)


def _strip_step_prefix(step: str) -> str:
    for prefix in _STEP_PREFIXES:
        if step.startswith(prefix):
            return step[len(prefix) :].strip()
    return step
