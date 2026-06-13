# RAG Embedding Backfill And Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe backfill and background indexing path so existing and failed RAG chunks can receive embeddings without duplicating the RAG service layer.

**Architecture:** Keep `RAGDocumentService` as the only service that knows how to embed and update document chunks. Add explicit chunk embedding status/error metadata, add a Celery-backed dispatcher matching the existing analysis job pattern, and expose an admin-only endpoint that can run eagerly in local mode or queue the reindex task in production.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Celery, pytest, PostgreSQL pgvector, AWS Bedrock Titan embeddings.

---

### Task 1: Chunk Embedding State

**Files:**
- Modify: `backend/app/models/rag_document.py`
- Modify: `backend/alembic/versions/20260523_07_add_rag_pgvector_embeddings.py`
- Modify: `backend/app/services/rag_document_service.py`
- Test: `backend/tests/test_rag_document_service.py`

- [x] **Step 1: Add failing tests that source creation marks successful embeddings as indexed and failed provider calls as failed without aborting source creation.**
- [x] **Step 2: Add `embedding_status`, `embedding_error`, and `embedding_attempts` to the chunk model and migration.**
- [x] **Step 3: Update chunk creation to store indexed or failed metadata while preserving existing source creation behavior.**
- [x] **Step 4: Run focused document-service tests.**

### Task 2: Backfill Service

**Files:**
- Modify: `backend/app/services/rag_document_service.py`
- Test: `backend/tests/test_rag_document_service.py`

- [x] **Step 1: Add failing tests for backfilling chunks with missing embeddings and retrying failed chunks.**
- [x] **Step 2: Implement `reindex_embeddings()` with source filter, limit, retry-failed control, and summary counts.**
- [x] **Step 3: Run focused document-service tests.**

### Task 3: Background Dispatch And Admin API

**Files:**
- Create: `backend/app/services/rag_indexing_service.py`
- Create: `backend/app/services/rag_indexing_worker.py`
- Modify: `backend/app/api/routes/rag.py`
- Modify: `backend/app/schemas/rag.py`
- Test: `backend/tests/test_rag_admin_routes.py`

- [x] **Step 1: Add failing admin route tests for dispatching a RAG embedding reindex request.**
- [x] **Step 2: Implement request/response schemas, dispatcher, Celery worker task, and admin route.**
- [x] **Step 3: Run focused admin route and indexing tests.**

### Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/AI_ML_RAG_DESIGN.md`
- Modify: `docs/SYSTEM_ARCHITECTURE.md`
- Modify: `docs/DEPLOYMENT_STRATEGY.md`
- Modify: `SYSTEM_AUDIT.md`
- Modify: `MEMORY.md`

- [x] **Step 1: Update docs to describe indexing/backfill, eager local mode, queued production mode, and remaining PDF parsing scope.**
- [x] **Step 2: Run focused RAG tests.**
- [x] **Step 3: Run backend compile and full backend tests.**
- [x] **Step 4: Run diff/status/whitespace checks and update this plan.**
