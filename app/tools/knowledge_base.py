from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.enums import TicketCategory


@dataclass(frozen=True)
class KnowledgeHit:
    doc_id: str
    title: str
    content: str
    score: float


class KnowledgeBase:
    """Small deterministic retriever used by tests and local development."""

    def __init__(self, docs: list[dict[str, str]] | None = None) -> None:
        self._docs = docs or self.default_docs()

    @staticmethod
    def default_docs() -> list[dict[str, str]]:
        return [
            {
                "doc_id": "kb-pairing-001",
                "title": "设备无法配网",
                "content": "请确认设备处于配网模式，Wi-Fi 仅支持 2.4GHz，并检查错误码是否为 E104。",
                "category": TicketCategory.NETWORK_PAIRING.value,
            },
            {
                "doc_id": "kb-device-001",
                "title": "设备故障排查",
                "content": "设备故障需要收集 SN、固件版本、指示灯状态和最近一次操作时间。",
                "category": TicketCategory.DEVICE_FAULT.value,
            },
            {
                "doc_id": "kb-refund-001",
                "title": "退款规则",
                "content": "退款必须校验订单状态、支付渠道与退款时效，客服不能承诺即时到账。",
                "category": TicketCategory.REFUND.value,
            },
            {
                "doc_id": "kb-account-001",
                "title": "账号安全",
                "content": "账号安全工单必须优先转人工，不通过自动化链路处理密码、验证码和身份信息。",
                "category": TicketCategory.ACCOUNT_SECURITY.value,
            },
        ]

    @classmethod
    def from_json(cls, path: Path) -> KnowledgeBase:
        import json

        docs = json.loads(path.read_text(encoding="utf-8"))
        return cls(docs=docs)

    def search(
        self,
        query: str,
        category: TicketCategory | None = None,
        top_k: int = 3,
    ) -> list[KnowledgeHit]:
        query_tokens = self._tokens(query)
        hits: list[KnowledgeHit] = []
        for doc in self._docs:
            if category and doc.get("category") not in {category.value, "all"}:
                category_bonus = 0.0
            else:
                category_bonus = 0.25

            doc_tokens = self._tokens(" ".join([doc["title"], doc["content"]]))
            overlap = len(query_tokens & doc_tokens)
            score = overlap / max(len(query_tokens), 1) + category_bonus
            if score > 0:
                hits.append(
                    KnowledgeHit(
                        doc_id=doc["doc_id"],
                        title=doc["title"],
                        content=doc["content"],
                        score=min(round(score, 4), 1.0),
                    )
                )

        hits.sort(key=lambda item: (-item.score, item.doc_id))
        return hits[:top_k]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        normalized = text.lower()
        ascii_tokens = {
            token.strip(".,;:!?()[]{}<>，。；：！？（）【】")
            for token in normalized.replace("/", " ").split()
            if token.strip()
        }
        char_tokens = {char for char in normalized if "\u4e00" <= char <= "\u9fff"}
        return ascii_tokens | char_tokens
