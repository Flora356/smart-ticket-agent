from __future__ import annotations

from app.agents.process_agent import ProcessAgent
from app.agents.qc_agent import QCAgent
from app.agents.respond_agent import RespondAgent
from app.agents.understand_agent import UnderstandAgent
from app.config import AppConfig
from app.orchestrator.workflow import TicketWorkflow
from app.providers.registry import build_provider
from app.storage.sqlite_repository import SQLiteTicketRepository
from app.tools.knowledge_base import KnowledgeBase
from app.tools.risk_scanner import RiskScanner
from app.tools.router import TicketRouter


class ApplicationContainer:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.from_env()
        self.repository = SQLiteTicketRepository(self.config.database_path)
        self.provider = build_provider(self.config)
        self.risk_scanner = RiskScanner()
        self.knowledge_base = KnowledgeBase()
        self.router = TicketRouter()

        self.understand_agent = UnderstandAgent(
            provider=self.provider,
            risk_scanner=self.risk_scanner,
            confidence_threshold=self.config.confidence_threshold,
        )
        self.process_agent = ProcessAgent(
            knowledge_base=self.knowledge_base,
            router=self.router,
        )
        self.respond_agent = RespondAgent(risk_scanner=self.risk_scanner)
        self.qc_agent = QCAgent(risk_scanner=self.risk_scanner)
        self.workflow = TicketWorkflow(
            repository=self.repository,
            understand_agent=self.understand_agent,
            process_agent=self.process_agent,
            respond_agent=self.respond_agent,
            qc_agent=self.qc_agent,
            max_retries=self.config.max_retries,
            auto_reply_enabled=self.config.auto_reply_enabled,
            model_name=self.provider.model_name,
        )

    def close(self) -> None:
        self.repository.close()
