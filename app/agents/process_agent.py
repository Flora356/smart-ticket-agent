from __future__ import annotations

from app.models.schemas import ProcessOutput, UnderstandOutput
from app.tools.knowledge_base import KnowledgeBase
from app.tools.router import TicketRouter


class ProcessAgent:
    name = "process_agent"

    def __init__(self, knowledge_base: KnowledgeBase, router: TicketRouter) -> None:
        self.knowledge_base = knowledge_base
        self.router = router

    def run(self, question: str, understood: UnderstandOutput) -> ProcessOutput:
        hits = self.knowledge_base.search(
            question,
            category=understood.category,
            top_k=3,
        )
        route = self.router.route(
            category=understood.category,
            priority=understood.priority,
            risk_flags=understood.risk_flags,
        )
        retrieval_confidence = hits[0].score if hits else 0.0

        return ProcessOutput(
            knowledge_hits=[f"{hit.doc_id}: {hit.content}" for hit in hits],
            assigned_group=route.group,
            route_reason=route.reason,
            need_human=understood.need_human or route.need_human,
            retrieval_confidence=retrieval_confidence,
        )
