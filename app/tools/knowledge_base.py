from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import TicketCategory


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_KB_PATH = PROJECT_ROOT / "configs" / "knowledge_base.json"


class KnowledgeDoc(BaseModel):
    """Schema for one knowledge base entry loaded from JSON."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    keywords: str = Field(min_length=1)
    content: str = Field(min_length=1)
    category: str = "all"

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        allowed = {category.value for category in TicketCategory} | {"all"}
        if value not in allowed:
            raise ValueError(f"unknown category '{value}', expected one of {sorted(allowed)}")
        return value


class KnowledgeDataset(BaseModel):
    """Schema for the whole knowledge base JSON file."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    description: str = ""
    docs: list[KnowledgeDoc] = Field(min_length=1)

    @field_validator("docs")
    @classmethod
    def validate_unique_ids(cls, docs: list[KnowledgeDoc]) -> list[KnowledgeDoc]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for doc in docs:
            if doc.doc_id in seen:
                duplicates.add(doc.doc_id)
            seen.add(doc.doc_id)
        if duplicates:
            raise ValueError(f"duplicate doc_id(s): {sorted(duplicates)}")
        return docs


@dataclass(frozen=True)
class KnowledgeHit:
    doc_id: str
    title: str
    content: str
    score: float


class KnowledgeBase:
    """Deterministic keyword retriever backed by a JSON knowledge base."""

    def __init__(
        self,
        docs: list[dict[str, str]] | None = None,
        path: Path | str | None = None,
    ) -> None:
        if docs is not None:
            self._docs = [KnowledgeDoc.model_validate(doc).model_dump() for doc in docs]
        else:
            self._docs = self.load_docs(path or DEFAULT_KB_PATH)

    @property
    def doc_count(self) -> int:
        return len(self._docs)

    @staticmethod
    def load_docs(path: Path | str) -> list[dict[str, str]]:
        """Read and validate a knowledge base JSON file.

        Raises pydantic.ValidationError when the file is malformed so a bad
        config fails loudly instead of silently degrading retrieval quality.
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        dataset = KnowledgeDataset.model_validate(raw)
        return [doc.model_dump() for doc in dataset.docs]

    @classmethod
    def from_json(cls, path: Path) -> KnowledgeBase:
        return cls(path=path)

    def search(
        self,
        query: str,
        category: TicketCategory | None = None,
        top_k: int = 3,
    ) -> list[KnowledgeHit]:
        normalized_query = query.lower()
        hits: list[KnowledgeHit] = []
        for doc in self._docs:
            score, matched = self._score(normalized_query, doc, category)
            if matched:
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
    def _score(
        query: str,
        doc: dict[str, str],
        category: TicketCategory | None,
    ) -> tuple[float, bool]:
        """Keyword-weighted scoring.

        A hit must share at least one real keyword with the document;
        single-character overlap alone does not count.
        """
        keywords = [k for k in doc.get("keywords", "").split() if k]
        matched = [keyword for keyword in keywords if keyword in query]

        title_tokens = [
            token
            for token in doc.get("title", "")
            .replace("（", " ")
            .replace("）", " ")
            .replace("/", " ")
            .split()
            if token
        ]
        matched_title = [token for token in title_tokens if token in query]

        if not matched and not matched_title:
            return 0.0, False

        keyword_score = min(len(matched) * 0.22, 0.66)
        title_score = min(len(matched_title) * 0.15, 0.3)

        category_bonus = 0.0
        doc_category = doc.get("category")
        if category and doc_category == category.value:
            category_bonus = 0.2
        elif category and doc_category == "all":
            category_bonus = 0.1

        return keyword_score + title_score + category_bonus, True
