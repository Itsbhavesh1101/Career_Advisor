from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RAGSourceType = Literal[
    "program",
    "counseling",
    "placement",
    "skill",
    "resume",
    "training",
    "policy",
]

RAGSourceStatus = Literal["active", "inactive"]
RAGReviewStatus = Literal["pending_review", "approved", "rejected"]


class RAGKnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chunk_id: str = Field(min_length=3, max_length=160)
    source_title: str = Field(min_length=2, max_length=220)
    source_type: RAGSourceType
    tags: list[str] = Field(default_factory=list, max_length=30)
    text: str = Field(min_length=20, max_length=2400)
    program_ids: list[str] = Field(default_factory=list, max_length=30)


class RAGEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chunk_id: str = Field(min_length=3, max_length=160)
    source_title: str = Field(min_length=2, max_length=220)
    source_type: RAGSourceType
    excerpt: str = Field(min_length=1, max_length=500)
    score: float = Field(ge=0)
    tags: list[str] = Field(default_factory=list, max_length=30)
    program_ids: list[str] = Field(default_factory=list, max_length=30)
    source_review_status: str | None = None
    source_freshness_status: str | None = None


class RAGSearchResponse(BaseModel):
    query: str
    results: list[RAGEvidence]


class RAGKnowledgeBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    version: str = Field(min_length=3, max_length=80)
    chunks: list[RAGKnowledgeChunk] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def _validate_unique_chunk_ids(self) -> "RAGKnowledgeBase":
        seen: set[str] = set()
        for chunk in self.chunks:
            if chunk.chunk_id in seen:
                raise ValueError(f"Duplicate chunk_id: {chunk.chunk_id}")
            seen.add(chunk.chunk_id)
        return self


class RAGDocumentSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=220)
    source_type: RAGSourceType
    text: str = Field(min_length=40, max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=30)
    program_ids: list[str] = Field(default_factory=list, max_length=30)


class RAGDocumentSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_type: str
    status: str
    review_status: str = "pending_review"
    review_notes: str | None = None
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    expires_at: datetime | None = None
    freshness_status: str = "current"
    tags: list[str]
    program_ids: list[str]
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class RAGDocumentSourceStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: RAGSourceStatus


class RAGDocumentSourceReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    review_status: RAGReviewStatus
    review_notes: str | None = Field(default=None, max_length=1000)
    expires_at: datetime | None = None


class RAGDocumentSourceList(BaseModel):
    items: list[RAGDocumentSourceRead]


class RAGEmbeddingIndexSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queued: bool = False
    source_id: int | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    examined: int = Field(default=0, ge=0)
    indexed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)


class RAGEmbeddingIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int | None = Field(default=None, ge=1)
    limit: int = Field(default=100, ge=1, le=1000)
    retry_failed: bool = True
