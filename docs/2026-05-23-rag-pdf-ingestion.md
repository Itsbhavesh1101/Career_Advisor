# RAG PDF Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let admins upload PDF/DOCX knowledge files into the existing DB-backed RAG pipeline.

**Architecture:** Add a focused parser service for PDF/DOCX bytes and keep `RAGDocumentService.create_source()` as the only ingestion path that creates sources, chunks, embeddings, and indexing metadata. Add an admin-only multipart endpoint that parses the uploaded file, maps form metadata to `RAGDocumentSourceCreate`, and returns the same source response contract as text-source creation. Expose the endpoint through the existing admin dashboard knowledge panel rather than creating a parallel ingestion workflow.

**Tech Stack:** FastAPI multipart uploads, pypdf, python-docx, SQLAlchemy, pytest.

---

### Task 1: RAG File Parser

**Files:**
- Create: `backend/app/services/rag_file_service.py`
- Test: `backend/tests/test_rag_file_service.py`

- [x] **Step 1: Add failing tests for DOCX extraction, PDF extraction, unsupported extension rejection, oversize rejection, and empty-text rejection.**
- [x] **Step 2: Implement PDF/DOCX byte parsing with bounded file size and normalized extracted text.**
- [x] **Step 3: Run focused parser tests.**

### Task 2: Multipart Admin Upload API

**Files:**
- Modify: `backend/app/api/routes/rag.py`
- Modify: `backend/tests/test_rag_admin_routes.py`

- [x] **Step 1: Add failing admin-route tests for successful file upload and non-admin rejection.**
- [x] **Step 2: Implement `POST /api/v1/rag/admin/sources/upload` using the parser service and existing `RAGDocumentService.create_source()`.**
- [x] **Step 3: Run focused RAG admin tests.**

### Task 3: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/AI_ML_RAG_DESIGN.md`
- Modify: `docs/FEATURE_SPEC.md`
- Modify: `docs/SYSTEM_ARCHITECTURE.md`
- Modify: `docs/DEPLOYMENT_STRATEGY.md`
- Modify: `SYSTEM_AUDIT.md`
- Modify: `MEMORY.md`

- [x] **Step 1: Update docs to describe PDF/DOCX RAG ingestion and remaining source-review/scheduled-indexing scope.**
- [x] **Step 2: Run focused RAG tests.**
- [x] **Step 3: Run backend compile and full backend tests.**
- [x] **Step 4: Run diff/status/whitespace checks and update this plan.**

### Task 4: Admin Dashboard Upload UX

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/AdminKnowledgePanel.tsx`
- Modify: `README.md`
- Modify: `docs/AI_ML_RAG_DESIGN.md`
- Modify: `docs/FEATURE_SPEC.md`
- Modify: `MEMORY.md`

- [x] **Step 1: Add a typed multipart upload helper for `POST /api/v1/rag/admin/sources/upload`.**
- [x] **Step 2: Add PDF/DOCX file upload controls to the existing admin knowledge panel without duplicating the ingestion path.**
- [x] **Step 3: Run frontend formatting/type/build checks.**
