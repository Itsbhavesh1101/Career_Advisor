from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.rag import (
    RAGEvidence,
    RAGKnowledgeBase,
    RAGKnowledgeChunk,
    RAGSourceType,
)

KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "configs" / "rag_knowledge.json"
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.]+")


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(value)}


@lru_cache(maxsize=1)
def _load_knowledge_base() -> RAGKnowledgeBase:
    with KNOWLEDGE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return RAGKnowledgeBase.model_validate(data)


class RAGService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def get_knowledge_base(self) -> RAGKnowledgeBase:
        return _load_knowledge_base().model_copy(deep=True)

    def list_chunks(self) -> list[RAGKnowledgeChunk]:
        chunks = (
            []
            if get_settings().institution_mode == "generic"
            else self.get_knowledge_base().chunks
        )
        if self.db is None:
            return chunks
        return chunks + self._list_active_document_chunks()

    def search(
        self,
        query: str,
        *,
        source_types: list[RAGSourceType] | None = None,
        program_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[RAGEvidence]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        query_tokens = _tokens(normalized_query)
        if not query_tokens:
            return []

        bounded_limit = max(1, limit)
        semantic_results = self._semantic_document_search(
            normalized_query,
            source_types=source_types,
            program_ids=program_ids,
            limit=bounded_limit,
        )
        lexical_results = self._lexical_search(
            query_tokens,
            source_types=source_types,
            program_ids=program_ids,
            limit=bounded_limit,
        )
        if not semantic_results:
            return lexical_results

        merged = list(semantic_results[:bounded_limit])
        seen_chunk_ids = {item.chunk_id for item in merged}
        for item in lexical_results:
            if item.chunk_id in seen_chunk_ids:
                continue
            merged.append(item)
            seen_chunk_ids.add(item.chunk_id)
            if len(merged) >= bounded_limit:
                break
        return merged

    def _lexical_search(
        self,
        query_tokens: set[str],
        *,
        source_types: list[RAGSourceType] | None = None,
        program_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[RAGEvidence]:
        allowed_source_types = set(source_types or [])
        requested_program_ids = set(program_ids or [])
        scored: list[tuple[float, RAGKnowledgeChunk]] = []

        for chunk in self.list_chunks():
            if allowed_source_types and chunk.source_type not in allowed_source_types:
                continue
            if requested_program_ids and not requested_program_ids.intersection(
                chunk.program_ids
            ):
                continue

            chunk_tokens = _tokens(
                " ".join([chunk.source_title, " ".join(chunk.tags), chunk.text])
            )
            overlap = query_tokens.intersection(chunk_tokens)
            if not overlap:
                continue

            tag_bonus = len(query_tokens.intersection(_tokens(" ".join(chunk.tags)))) * 0.5
            program_bonus = 1.0 if requested_program_ids.intersection(chunk.program_ids) else 0.0
            score = float(len(overlap)) + tag_bonus + program_bonus
            scored.append((score, chunk))

        bounded_limit = max(1, limit)
        scored.sort(key=lambda item: (-item[0], item[1].source_title, item[1].chunk_id))
        return [
            RAGEvidence(
                chunk_id=chunk.chunk_id,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                excerpt=self._excerpt(chunk.text, query_tokens),
                score=score,
                tags=chunk.tags,
                program_ids=chunk.program_ids,
            )
            for score, chunk in scored[:bounded_limit]
        ]

    def _semantic_document_search(
        self,
        query: str,
        *,
        source_types: list[RAGSourceType] | None,
        program_ids: list[str] | None,
        limit: int,
    ) -> list[RAGEvidence]:
        if self.db is None or not get_settings().rag_vector_search_enabled:
            return []
        try:
            from app.services.rag_document_service import RAGDocumentService

            return RAGDocumentService(self.db).semantic_search(
                query,
                source_types=source_types,
                program_ids=program_ids,
                limit=limit,
            )
        except Exception:
            return []

    def _excerpt(self, text: str, query_tokens: set[str], max_chars: int = 360) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        best = max(
            sentences,
            key=lambda sentence: len(query_tokens.intersection(_tokens(sentence))),
            default=text,
        )
        if len(best) <= max_chars:
            return best
        return best[: max_chars - 3].rstrip() + "..."

    def _list_active_document_chunks(self) -> list[RAGKnowledgeChunk]:
        if self.db is None:
            return []
        from app.services.rag_document_service import RAGDocumentService

        return RAGDocumentService(self.db).list_active_chunks()
