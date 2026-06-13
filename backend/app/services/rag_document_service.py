from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, text as sql_text
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.rag_document import RAGDocumentChunk, RAGDocumentSource
from app.schemas.rag import (
    RAGEvidence,
    RAGDocumentSourceCreate,
    RAGDocumentSourceRead,
    RAGDocumentSourceReviewUpdate,
    RAGEmbeddingIndexSummary,
    RAGKnowledgeChunk,
    RAGSourceStatus,
    RAGSourceType,
)
from app.services.embedding_service import (
    cosine_similarity,
    create_embedding_provider,
    parse_vector_literal,
    vector_literal,
)
from app.services.rag_service import _tokens


class RAGDocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def chunk_text(self, text: str, *, max_chars: int = 900) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        bounded_max = max(100, max_chars)
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]

        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if len(sentence) > bounded_max:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long_sentence(sentence, bounded_max))
                continue

            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > bounded_max:
                chunks.append(current)
                current = sentence
            else:
                current = candidate

        if current:
            chunks.append(current)
        return chunks

    def create_source(
        self,
        payload: RAGDocumentSourceCreate,
        created_by_user_id: int | None,
    ) -> RAGDocumentSource:
        normalized_text = " ".join(payload.text.split())
        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        source_nonce = uuid4().hex[:12]
        now = datetime.now(timezone.utc)

        source = RAGDocumentSource(
            title=payload.title,
            source_type=payload.source_type,
            status="active",
            tags=list(payload.tags),
            program_ids=list(payload.program_ids),
            content_hash=content_hash,
            review_status="pending_review",
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
        )
        embedding_provider = create_embedding_provider()
        source.chunks = [
            self._chunk_to_model(
                chunk=chunk,
                chunk_id=f"doc-{content_hash[:8]}-{source_nonce}-{index:04d}",
                chunk_index=index,
                payload=payload,
                created_at=now,
                embedding_provider=embedding_provider,
            )
            for index, chunk in enumerate(self.chunk_text(payload.text))
        ]

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def list_sources(self) -> list[RAGDocumentSourceRead]:
        rows = self._source_rows()
        return [
            RAGDocumentSourceRead.model_validate(
                {
                    "id": source.id,
                    "title": source.title,
                    "source_type": source.source_type,
                    "status": source.status,
                    "review_status": getattr(source, "review_status", "approved"),
                    "review_notes": getattr(source, "review_notes", None),
                    "reviewed_by_user_id": getattr(
                        source, "reviewed_by_user_id", None
                    ),
                    "reviewed_at": getattr(source, "reviewed_at", None),
                    "expires_at": getattr(source, "expires_at", None),
                    "freshness_status": self._freshness_status(source),
                    "tags": list(source.tags or []),
                    "program_ids": list(source.program_ids or []),
                    "chunk_count": len(
                        [
                            chunk
                            for chunk in getattr(source, "chunks", []) or []
                            if getattr(chunk, "is_active", False)
                        ]
                    ),
                    "created_at": source.created_at,
                    "updated_at": source.updated_at,
                }
            )
            for source in rows
        ]

    def update_status(
        self,
        source_id: int,
        status: RAGSourceStatus,
    ) -> RAGDocumentSource:
        source = self.db.get(RAGDocumentSource, source_id)
        if source is None:
            raise ValueError("RAG document source not found")

        is_active = status == "active"
        source.status = status
        source.updated_at = datetime.now(timezone.utc)
        chunks = list(getattr(source, "chunks", []) or [])
        if not chunks:
            chunks = list(
                self.db.scalars(
                    select(RAGDocumentChunk).where(RAGDocumentChunk.source_id == source.id)
                ).all()
            )
        for chunk in chunks:
            chunk.is_active = is_active

        self.db.commit()
        self.db.refresh(source)
        return source

    def update_review(
        self,
        source_id: int,
        payload: RAGDocumentSourceReviewUpdate,
        reviewed_by_user_id: int | None,
    ) -> RAGDocumentSource:
        source = self.db.get(RAGDocumentSource, source_id)
        if source is None:
            raise ValueError("RAG document source not found")

        source.review_status = payload.review_status
        source.review_notes = payload.review_notes
        source.reviewed_by_user_id = reviewed_by_user_id
        source.reviewed_at = datetime.now(timezone.utc)
        source.expires_at = payload.expires_at
        source.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(source)
        return source

    def list_active_chunks(self) -> list[RAGKnowledgeChunk]:
        chunks: list[RAGKnowledgeChunk] = []
        for source in self._reviewed_active_source_rows():
            for chunk in getattr(source, "chunks", []) or []:
                if not getattr(chunk, "is_active", False):
                    continue
                chunks.append(
                    RAGKnowledgeChunk(
                        chunk_id=chunk.chunk_id,
                        source_title=chunk.source_title,
                        source_type=chunk.source_type,
                        tags=list(chunk.tags or []),
                        text=chunk.text,
                        program_ids=list(chunk.program_ids or []),
                    )
                )
        chunks.sort(key=lambda item: (item.source_title, item.chunk_id))
        return chunks

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

        allowed_source_types = set(source_types or [])
        requested_program_ids = set(program_ids or [])
        scored: list[tuple[float, RAGKnowledgeChunk]] = []

        for chunk in self.list_active_chunks():
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
            program_bonus = (
                1.0 if requested_program_ids.intersection(chunk.program_ids) else 0.0
            )
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
                source_review_status="approved",
                source_freshness_status="current",
            )
            for score, chunk in scored[:bounded_limit]
        ]

    def semantic_search(
        self,
        query: str,
        *,
        source_types: list[RAGSourceType] | None = None,
        program_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[RAGEvidence]:
        normalized_query = query.strip()
        query_tokens = _tokens(normalized_query)
        if not normalized_query or not query_tokens:
            return []

        bounded_limit = max(1, limit)
        try:
            provider = create_embedding_provider()
            query_embedding = provider.embed(normalized_query)
        except Exception:
            return []

        pgvector_results = self._semantic_pgvector_search(
            query_embedding_literal=vector_literal(query_embedding.values),
            query_tokens=query_tokens,
            dimensions=query_embedding.dimensions,
            source_types=source_types,
            program_ids=program_ids,
            limit=bounded_limit,
        )
        if pgvector_results:
            return pgvector_results

        return self._semantic_in_memory_search(
            query_embedding=query_embedding.values,
            query_tokens=query_tokens,
            dimensions=query_embedding.dimensions,
            source_types=source_types,
            program_ids=program_ids,
            limit=bounded_limit,
        )

    def reindex_embeddings(
        self,
        *,
        source_id: int | None = None,
        limit: int = 100,
        retry_failed: bool = True,
    ) -> RAGEmbeddingIndexSummary:
        bounded_limit = max(1, min(limit, 1000))
        summary = RAGEmbeddingIndexSummary(source_id=source_id, limit=bounded_limit)
        provider = create_embedding_provider()
        now = datetime.now(timezone.utc)

        for chunk in self._chunks_needing_embedding(
            provider=provider,
            source_id=source_id,
            limit=bounded_limit,
            retry_failed=retry_failed,
        ):
            summary.examined += 1
            if not getattr(chunk, "is_active", False):
                summary.skipped += 1
                continue
            if self._apply_embedding_to_chunk(chunk, provider=provider, now=now):
                summary.indexed += 1
            else:
                summary.failed += 1

        if summary.examined:
            self.db.commit()
        return summary

    def _source_rows(self, *, status: RAGSourceStatus | None = None) -> list[RAGDocumentSource]:
        stmt = (
            select(RAGDocumentSource)
            .options(selectinload(RAGDocumentSource.chunks))
            .order_by(RAGDocumentSource.created_at.desc(), RAGDocumentSource.id.desc())
        )
        if status is not None:
            stmt = stmt.where(RAGDocumentSource.status == status)
        rows = self.db.scalars(stmt).all()
        if status is None:
            return list(rows)
        return [source for source in rows if source.status == status]

    def _reviewed_active_source_rows(self) -> list[RAGDocumentSource]:
        now = datetime.now(timezone.utc)
        return [
            source
            for source in self._source_rows(status="active")
            if getattr(source, "review_status", "approved") == "approved"
            and (
                getattr(source, "expires_at", None) is None
                or self._coerce_datetime(getattr(source, "expires_at")) > now
            )
        ]

    def _freshness_status(self, source: RAGDocumentSource) -> str:
        expires_at = getattr(source, "expires_at", None)
        if expires_at is None:
            return "current"
        return (
            "expired"
            if self._coerce_datetime(expires_at) <= datetime.now(timezone.utc)
            else "current"
        )

    def _coerce_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _split_long_sentence(self, sentence: str, max_chars: int) -> list[str]:
        chunks: list[str] = []
        current = ""
        for word in sentence.split():
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = word
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def _chunk_to_model(
        self,
        *,
        chunk: str,
        chunk_id: str,
        chunk_index: int,
        payload: RAGDocumentSourceCreate,
        created_at: datetime,
        embedding_provider,
    ) -> RAGDocumentChunk:
        row = RAGDocumentChunk(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            source_title=payload.title,
            source_type=payload.source_type,
            text=chunk,
            tags=list(payload.tags),
            program_ids=list(payload.program_ids),
            is_active=True,
            created_at=created_at,
        )
        self._apply_embedding_to_chunk(row, provider=embedding_provider, now=created_at)
        return row

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

    def _semantic_pgvector_search(
        self,
        *,
        query_embedding_literal: str,
        query_tokens: set[str],
        dimensions: int,
        source_types: list[RAGSourceType] | None,
        program_ids: list[str] | None,
        limit: int,
    ) -> list[RAGEvidence]:
        if not hasattr(self.db, "execute"):
            return []

        settings = get_settings()
        candidate_limit = max(limit * 50, 200)
        stmt = sql_text(
            """
            SELECT
                chunk_id,
                source_title,
                source_type,
                text,
                tags,
                program_ids,
                1 - (embedding <=> CAST(:query_embedding AS extensions.vector)) AS score
            FROM rag_document_chunks
            WHERE is_active = true
              AND embedding IS NOT NULL
              AND embedding_status = 'indexed'
              AND embedding_dimensions = :dimensions
              AND source_id IN (
                SELECT id
                FROM rag_document_sources
                WHERE status = 'active'
                  AND review_status = 'approved'
                  AND (expires_at IS NULL OR expires_at > NOW())
              )
            ORDER BY embedding <=> CAST(:query_embedding AS extensions.vector)
            LIMIT :candidate_limit
            """
        )
        try:
            rows = (
                self.db.execute(
                    stmt,
                    {
                        "query_embedding": query_embedding_literal,
                        "dimensions": dimensions,
                        "candidate_limit": candidate_limit,
                    },
                )
                .mappings()
                .all()
            )
        except Exception:
            return []

        return self._evidence_from_rows(
            rows,
            query_tokens=query_tokens,
            source_types=source_types,
            program_ids=program_ids,
            limit=limit,
            min_score=settings.rag_semantic_min_score,
        )

    def _semantic_in_memory_search(
        self,
        *,
        query_embedding: list[float],
        query_tokens: set[str],
        dimensions: int,
        source_types: list[RAGSourceType] | None,
        program_ids: list[str] | None,
        limit: int,
    ) -> list[RAGEvidence]:
        allowed_source_types = set(source_types or [])
        requested_program_ids = set(program_ids or [])
        scored: list[tuple[float, RAGDocumentChunk]] = []

        for source in self._reviewed_active_source_rows():
            for chunk in getattr(source, "chunks", []) or []:
                if not getattr(chunk, "is_active", False):
                    continue
                if allowed_source_types and chunk.source_type not in allowed_source_types:
                    continue
                if requested_program_ids and not requested_program_ids.intersection(
                    set(chunk.program_ids or [])
                ):
                    continue
                if chunk.embedding_dimensions != dimensions:
                    continue
                if getattr(chunk, "embedding_status", "indexed") != "indexed":
                    continue
                chunk_embedding = parse_vector_literal(chunk.embedding)
                if chunk_embedding is None:
                    continue
                score = cosine_similarity(query_embedding, chunk_embedding)
                if score <= get_settings().rag_semantic_min_score:
                    continue
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].source_title, item[1].chunk_id))
        return [
            RAGEvidence(
                chunk_id=chunk.chunk_id,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                excerpt=self._excerpt(chunk.text, query_tokens),
                score=max(score, 0.0),
                tags=list(chunk.tags or []),
                program_ids=list(chunk.program_ids or []),
                source_review_status="approved",
                source_freshness_status="current",
            )
            for score, chunk in scored[:limit]
        ]

    def _evidence_from_rows(
        self,
        rows: list[object],
        *,
        query_tokens: set[str],
        source_types: list[RAGSourceType] | None,
        program_ids: list[str] | None,
        limit: int,
        min_score: float,
    ) -> list[RAGEvidence]:
        allowed_source_types = set(source_types or [])
        requested_program_ids = set(program_ids or [])
        results: list[RAGEvidence] = []

        for row in rows:
            source_type = _row_value(row, "source_type")
            row_program_ids = _string_list(_row_value(row, "program_ids"))
            if allowed_source_types and source_type not in allowed_source_types:
                continue
            if requested_program_ids and not requested_program_ids.intersection(
                row_program_ids
            ):
                continue

            score = max(float(_row_value(row, "score") or 0.0), 0.0)
            if score <= min_score:
                continue
            results.append(
                RAGEvidence(
                    chunk_id=str(_row_value(row, "chunk_id")),
                    source_title=str(_row_value(row, "source_title")),
                    source_type=source_type,
                    excerpt=self._excerpt(str(_row_value(row, "text")), query_tokens),
                    score=score,
                    tags=_string_list(_row_value(row, "tags")),
                    program_ids=row_program_ids,
                    source_review_status="approved",
                    source_freshness_status="current",
                )
            )
            if len(results) >= limit:
                break

        return results

    def _chunks_needing_embedding(
        self,
        *,
        provider,
        source_id: int | None,
        limit: int,
        retry_failed: bool,
    ) -> list[RAGDocumentChunk]:
        if hasattr(self.db, "sources"):
            candidates: list[RAGDocumentChunk] = []
            for source in self._source_rows(status="active"):
                if source_id is not None and source.id != source_id:
                    continue
                for chunk in getattr(source, "chunks", []) or []:
                    if self._needs_embedding(
                        chunk,
                        provider=provider,
                        retry_failed=retry_failed,
                    ):
                        candidates.append(chunk)
                    if len(candidates) >= limit:
                        return candidates
            return candidates

        stmt = (
            select(RAGDocumentChunk)
            .where(RAGDocumentChunk.is_active.is_(True))
            .order_by(RAGDocumentChunk.id.asc())
            .limit(limit * 5)
        )
        if source_id is not None:
            stmt = stmt.where(RAGDocumentChunk.source_id == source_id)
        rows = list(self.db.scalars(stmt).all())
        return [
            chunk
            for chunk in rows
            if self._needs_embedding(
                chunk,
                provider=provider,
                retry_failed=retry_failed,
            )
        ][:limit]

    def _needs_embedding(
        self,
        chunk: RAGDocumentChunk,
        *,
        provider,
        retry_failed: bool,
    ) -> bool:
        status = getattr(chunk, "embedding_status", "pending")
        if status == "failed" and not retry_failed:
            return False
        if not getattr(chunk, "is_active", False):
            return False
        return (
            not getattr(chunk, "embedding", None)
            or status != "indexed"
            or getattr(chunk, "embedding_provider", None) != provider.provider
            or getattr(chunk, "embedding_model", None) != provider.model
            or getattr(chunk, "embedding_dimensions", None) != provider.dimensions
        )

    def _apply_embedding_to_chunk(self, chunk: RAGDocumentChunk, *, provider, now: datetime) -> bool:
        chunk.embedding_attempts = int(getattr(chunk, "embedding_attempts", 0) or 0) + 1
        chunk.embedding_provider = provider.provider
        chunk.embedding_model = provider.model
        chunk.embedding_dimensions = provider.dimensions
        chunk.embedding_updated_at = now
        try:
            embedding = provider.embed(self._chunk_embedding_text(chunk))
        except Exception as exc:
            if not getattr(chunk, "embedding", None):
                chunk.embedding_status = "failed"
            chunk.embedding_error = str(exc)[:500]
            return False

        chunk.embedding = vector_literal(embedding.values)
        chunk.embedding_provider = embedding.provider
        chunk.embedding_model = embedding.model
        chunk.embedding_dimensions = embedding.dimensions
        chunk.embedding_status = "indexed"
        chunk.embedding_error = None
        chunk.embedding_updated_at = now
        return True

    def _chunk_embedding_text(self, chunk: RAGDocumentChunk) -> str:
        return " ".join(
            [
                str(chunk.source_title),
                " ".join(str(tag) for tag in (chunk.tags or [])),
                str(chunk.text),
            ]
        )


def _row_value(row: object, key: str) -> object:
    if hasattr(row, "get"):
        return row.get(key)
    return getattr(row, key)


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []
