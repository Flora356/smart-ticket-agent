from __future__ import annotations

from app.models.schemas import ProcessOutput, RespondOutput, UnderstandOutput
from app.tools.risk_scanner import RiskScanner


class RespondAgent:
    name = "respond_agent"

    def __init__(self, risk_scanner: RiskScanner) -> None:
        self.risk_scanner = risk_scanner

    def run(
        self,
        question: str,
        understood: UnderstandOutput,
        processed: ProcessOutput,
    ) -> RespondOutput:
        citations = [hit.split(":", 1)[0] for hit in processed.knowledge_hits]

        if processed.need_human:
            draft = (
                "您好，该问题涉及较高风险或需要人工核验，已为您转交对应支持团队。"
                "请保留设备 SN、订单号或截图，工作人员会尽快跟进。"
            )
            confidence = 0.9
        elif processed.knowledge_hits:
            evidence = processed.knowledge_hits[0].split(": ", 1)[-1]
            draft = (
                f"您好，关于「{understood.normalized_question}」，"
                f"初步处理建议如下：{evidence}"
                " 如果问题仍未解决，请补充设备型号、SN 和错误截图，我们将继续排查。"
            )
            confidence = min(0.92, 0.65 + processed.retrieval_confidence)
        else:
            draft = (
                "您好，目前知识库中没有完全匹配的处理方案，已转交人工支持。"
                "请补充设备型号、SN、错误码或订单信息。"
            )
            confidence = 0.55

        risk = self.risk_scanner.scan(draft)
        return RespondOutput(
            reply_draft=draft,
            citations=citations,
            risk_flags=sorted(set(understood.risk_flags + risk.flags)),
            confidence=confidence,
        )
