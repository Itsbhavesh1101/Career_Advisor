# System Architecture

## Architecture Summary

SAGE AI Career Navigator is a full-stack institutional platform with a Next.js frontend, FastAPI backend, PostgreSQL database, configurable SAGE institution model, AI service layer, seeded plus admin-managed RAG evidence foundation, pgvector-ready semantic RAG for admin text sources, deterministic agentic snapshot orchestration, admission intelligence aggregation, and placement intelligence aggregation.

## Current Runtime Flow

1. User authenticates through frontend.
2. Frontend sends API requests to FastAPI.
3. FastAPI validates auth and request payloads.
4. Service layer reads and writes PostgreSQL data.
5. Institution services load the SAGE catalog and merge admin overrides.
6. RAG service retrieves curated seeded evidence and active approved current DB-backed admin knowledge from manual text and uploaded PDF/DOCX sources for twelfth-student program-fit analysis, preferring pgvector semantic matches for embedded admin chunks when available.
7. AI-related services call the current provider-backed LLM client.
8. Strict schemas validate AI output, including program-fit and counselor expectation fields.
9. Retrieved RAG evidence is persisted with the analysis.
10. Analysis snapshot service records agent stages and verifier output in async job summaries.
11. Admission Intelligence service derives admin-only counseling metrics and lead cards from twelfth-student profiles plus latest program-fit analyses.
12. Placement Intelligence service derives admin-only placement metrics, evidence ledgers, company readiness radar, faculty notes, and training ROI signals from college-student profiles plus latest readiness records.
13. Frontend renders student, analysis, resume, evidence, agentic pipeline, admin dashboards, the Admission Intelligence panel, the Placement Intelligence panel, and the admin RAG knowledge panel.

## Current Backend Boundaries

- `backend/app/api/routes`: HTTP route handlers.
- `backend/app/services`: business logic and AI module services.
- `backend/app/schemas`: Pydantic request and response contracts.
- `backend/app/models`: SQLAlchemy models.
- `backend/app/core`: configuration, auth, errors, rate limits, scoring, retention.
- `backend/alembic`: database migrations.

## Phase 2 Configurable Institution Model

Phase 2 adds the configurable SAGE institution catalog, program-fit analysis contract, counselor expectation checks, and admin override API. The previous AIML/Cyber-specific fields remain available as compatibility fields during the transition.

## Phase 4 Seeded RAG Foundation

Phase 4 adds deterministic seeded RAG retrieval over curated SAGE/SIRT knowledge. The backend exposes authenticated RAG search, program-fit generation receives bounded evidence context, `career_analyses.rag_evidence` stores retrieved snippets, and the frontend renders evidence used in the Program Intelligence panel.

## Phase 5 Agentic Snapshot Foundation

Phase 5 wraps existing analysis modules in a deterministic agentic snapshot. `AnalysisSnapshotService` records stage metadata for profile understanding, program fit or career pathway generation, placement risk, internship readiness, employability, company readiness, role gaps, and verifier review. `AnalysisVerifierService` produces status, confidence, evidence count, warnings, blockers, and next-best actions. The existing `analysis_jobs.snapshot_summary` JSON persists the snapshot; no new table is required.

## Phase 6 Document RAG Expansion

Phase 6 adds DB-backed institutional knowledge sources. `RAGFileService` validates and extracts PDF/DOCX upload text, then `RAGDocumentService` chunks admin-submitted or parsed text, persists sources and chunks, generates embeddings for new chunks, exposes reviewed active chunks as `RAGKnowledgeChunk` objects, supports source activation or deactivation, and backfills missing or failed embeddings in bounded batches. `RAGService` keeps seeded JSON knowledge as the immutable base, prefers semantic admin-document matches through pgvector when available, and merges lexical evidence as fallback/fill when initialized with a database session. Admin APIs, the admin dashboard panel, `POST /api/v1/rag/admin/sources/upload`, and `POST /api/v1/rag/admin/embeddings/reindex` provide the current governance and indexing surface.

The institutional readiness wave promotes source review into the current baseline. `rag_document_sources` now stores review status, review notes, reviewer, review timestamp, and expiry. New admin sources default to pending review; migrated sources are approved; retrieval excludes pending, rejected, or expired admin sources. Scheduled recurring indexing remains a target-state upgrade.

## Phase 7 Admission Intelligence Baseline

Phase 7 adds `AdmissionIntelligenceService`, an admin-only deterministic aggregation layer over existing `student_profiles` and latest `career_analyses`. It does not add admission CRM tables yet. The service computes twelfth-student admission metrics, high-intent flags, wrong-branch-risk status, lost-reason signals, and Counselor Copilot briefs from existing program-fit fields and RAG evidence. The FastAPI route exposes `/api/v1/admission-intelligence/dashboard`, and the admin dashboard renders the compact command panel.

## Phase 8 Placement Intelligence Baseline

Phase 8 adds `PlacementIntelligenceService`, an admin-only deterministic aggregation layer over existing college-student profiles and latest employability, placement risk, company fit, role gap, career analysis, and internship readiness records. The service computes placement metrics, Skill Evidence Ledger scores, AI Placement War Room priority cards, Company-Specific Readiness Radar buckets, Training ROI signals, and Faculty Advisor notes. The FastAPI route exposes `/api/v1/placement-intelligence/dashboard`, and the admin dashboard renders the compact command panel below Admission Intelligence.

Placement operations are handled by the focused `placement_opportunities` and `placement_applications` tables rather than a duplicate ATS module. `/api/v1/placement-opportunities` exposes admin opportunity CRUD, filtered CSV export, application review/status updates, and student matched-opportunity application actions. The student internship page consumes the same module for matched opportunities and application next steps, while the admin Placements tab uses it for opportunity board and applicant review workflows.

## Current Frontend Boundaries

- `frontend/app`: route pages.
- `frontend/components`: reusable UI components.
- `frontend/lib`: API client and local profile helpers.
- `frontend/public`: static assets.

## Current Intelligence Architecture

The current analysis job flow acts as a deterministic Analysis Orchestrator.

The orchestrator coordinates:

- Profile Understanding Agent.
- Program Fit Agent.
- Career Pathway Agent.
- Skill Gap Agent.
- Resume Agent.
- Placement Risk Agent.
- Training Strategy Agent.
- Verifier Agent.

## Target Data Flow

1. Student or counselor creates profile.
2. System retrieves relevant SAGE program knowledge from seeded and admin-managed RAG, preferring semantic vector matches for embedded admin chunks.
3. Deterministic scoring calculates base readiness and fit.
4. Provider-backed AI services generate structured analysis through the OpenAI-compatible or AWS Bedrock provider.
5. Verifier checks module completeness, evidence count, warnings, blockers, and consistency.
6. System stores one coherent student intelligence snapshot.
7. Admission Intelligence derives counselor-facing metrics and intervention lists from the latest twelfth-student snapshots.
8. Placement Intelligence derives placement-cell metrics, evidence gaps, company readiness, faculty notes, and training ROI from the latest college-student readiness records.
9. Student, counselor, faculty, placement cell, and leadership dashboards show role-specific views.

## Target Deployment Architecture

- Browser -> Vercel Next.js frontend.
- Next.js frontend -> Google Cloud Run FastAPI backend.
- FastAPI backend -> Supabase Postgres.
- FastAPI backend -> AWS Bedrock for LLM inference.
- FastAPI backend -> seeded JSON plus DB-backed admin RAG retrieval from text/PDF/DOCX sources, with pgvector semantic retrieval for embedded admin chunks, lexical fallback, and Celery-backed embedding reindexing.
- FastAPI backend -> admin readiness and student dashboard summary APIs for launch operations without adding a full CRM/ATS.

## Phase 9 Launch Readiness

Phase 9 adds deployment artifacts without changing runtime business behavior. `backend/Dockerfile` packages the FastAPI backend for Cloud Run and starts Uvicorn with the Cloud Run `PORT` contract. `deploy/cloud-run/backend.env.yaml.example` captures production settings without secrets, while `deploy-backend.ps1` and `deploy-backend.sh` provide repeatable `gcloud run deploy` commands. The Cloud Run runbook documents migrations, Vercel `NEXT_PUBLIC_API_BASE_URL`, smoke tests, rollback, and launch cost controls. The Bedrock runbook documents the existing provider abstraction, Converse API usage, `BEDROCK_MODEL_ID`, `ap-south-1`, IAM, and credential strategy.

## Architecture Principles

- Preserve current working behavior.
- Use the configurable institution catalog for program and branch logic; keep AIML/Cyber fields only as transition compatibility fields.
- Keep deterministic scoring for explainability.
- Use LLMs for reasoning, synthesis, and language generation.
- Validate all AI outputs.
- Attach evidence and confidence to recommendations.
- Keep deployment low-cost and scalable.
