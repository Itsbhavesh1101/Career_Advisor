from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user_context, get_db
from app.models.user import User
from app.schemas.rag import (
    RAGDocumentSourceCreate,
    RAGDocumentSourceList,
    RAGDocumentSourceRead,
    RAGDocumentSourceReviewUpdate,
    RAGDocumentSourceStatusUpdate,
    RAGEmbeddingIndexRequest,
    RAGEmbeddingIndexSummary,
    RAGSearchResponse,
    RAGSourceType,
)
from app.services.rag_document_service import RAGDocumentService
from app.services.rag_file_service import RAGFileParseError, RAGFileService
from app.services.rag_indexing_service import dispatch_rag_embedding_reindex
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search", response_model=RAGSearchResponse)
def search_rag(
    q: str = Query(min_length=1, max_length=500),
    source_type: list[RAGSourceType] | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=10),
    _context=Depends(get_current_user_context),
    db: Session = Depends(get_db),
) -> RAGSearchResponse:
    results = RAGService(db).search(q, source_types=source_type, limit=limit)
    return RAGSearchResponse(query=q, results=results)


@router.post("/admin/sources", response_model=RAGDocumentSourceRead)
def create_rag_source(
    payload: RAGDocumentSourceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RAGDocumentSourceRead:
    source = RAGDocumentService(db).create_source(
        payload,
        created_by_user_id=getattr(admin, "id", None),
    )
    return _source_to_read(source)


@router.post("/admin/sources/upload", response_model=RAGDocumentSourceRead)
async def upload_rag_source_file(
    title: str = Form(min_length=3, max_length=220),
    source_type: RAGSourceType = Form(),
    tags: str = Form(default=""),
    program_ids: str = Form(default=""),
    file: UploadFile = File(),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RAGDocumentSourceRead:
    payload = await file.read()
    try:
        text = RAGFileService().extract_text(file.filename or "knowledge.pdf", payload)
    except RAGFileParseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    source = RAGDocumentService(db).create_source(
        RAGDocumentSourceCreate(
            title=title,
            source_type=source_type,
            text=text,
            tags=_split_form_list(tags),
            program_ids=_split_form_list(program_ids),
        ),
        created_by_user_id=getattr(admin, "id", None),
    )
    return _source_to_read(source)


@router.get("/admin/sources", response_model=RAGDocumentSourceList)
def list_rag_sources(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RAGDocumentSourceList:
    sources = RAGDocumentService(db).list_sources()
    return RAGDocumentSourceList(items=sources)


@router.patch("/admin/sources/{source_id}/status", response_model=RAGDocumentSourceRead)
def update_rag_source_status(
    source_id: int,
    payload: RAGDocumentSourceStatusUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RAGDocumentSourceRead:
    try:
        source = RAGDocumentService(db).update_status(source_id, payload.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG document source not found",
        ) from exc
    return _source_to_read(source)


@router.patch("/admin/sources/{source_id}/review", response_model=RAGDocumentSourceRead)
def update_rag_source_review(
    source_id: int,
    payload: RAGDocumentSourceReviewUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> RAGDocumentSourceRead:
    try:
        source = RAGDocumentService(db).update_review(
            source_id,
            payload,
            reviewed_by_user_id=getattr(admin, "id", None),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG document source not found",
        ) from exc
    return _source_to_read(source)


@router.post(
    "/admin/embeddings/reindex",
    response_model=RAGEmbeddingIndexSummary,
)
def reindex_rag_embeddings(
    payload: RAGEmbeddingIndexRequest,
    _admin: User = Depends(get_current_admin),
) -> RAGEmbeddingIndexSummary:
    return dispatch_rag_embedding_reindex(
        source_id=payload.source_id,
        limit=payload.limit,
        retry_failed=payload.retry_failed,
    )


def _split_form_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _source_to_read(source) -> RAGDocumentSourceRead:
    if isinstance(source, RAGDocumentSourceRead):
        return source

    chunks = list(getattr(source, "chunks", []) or [])
    return RAGDocumentSourceRead.model_validate(
        {
            "id": source.id,
            "title": source.title,
            "source_type": source.source_type,
            "status": source.status,
            "review_status": getattr(source, "review_status", "approved"),
            "review_notes": getattr(source, "review_notes", None),
            "reviewed_by_user_id": getattr(source, "reviewed_by_user_id", None),
            "reviewed_at": getattr(source, "reviewed_at", None),
            "expires_at": getattr(source, "expires_at", None),
            "freshness_status": _freshness_status(source),
            "tags": list(source.tags or []),
            "program_ids": list(source.program_ids or []),
            "chunk_count": len(
                [chunk for chunk in chunks if getattr(chunk, "is_active", False)]
            ),
            "created_at": source.created_at,
            "updated_at": source.updated_at,
        }
    )


def _freshness_status(source) -> str:
    expires_at = getattr(source, "expires_at", None)
    if expires_at is None:
        return "current"
    from datetime import datetime, timezone

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return "expired" if expires_at <= datetime.now(timezone.utc) else "current"
