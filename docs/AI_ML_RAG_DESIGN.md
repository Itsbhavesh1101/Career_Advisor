# AI, ML, And RAG Design

## Design Goal

Build an institution-specific intelligence layer that combines deterministic scoring, a configurable SAGE program catalog, selectable LLM providers, seeded plus admin-managed RAG evidence, deterministic agentic snapshots, semantic RAG expansion, and verifier checks.

## Current AI Baseline

- Phase 3 provider abstraction for LLM inference.
- OpenAI-compatible provider remains supported.
- AWS Bedrock is selectable with `LLM_PROVIDER=bedrock`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`.
- Strict Pydantic schemas.
- JSON repair and normalization.
- Cost controls.
- Circuit breaker.
- Endpoint-specific budgets.
- Psychometric fallback mode.
- Configurable SAGE institution catalog.
- Program-fit analysis contract with counselor expectation reality checks.
- Seeded RAG retrieval over curated SAGE/SIRT knowledge.
- DB-backed admin-managed text knowledge sources and chunks.
- Admin PDF/DOCX knowledge ingestion through the same DB-backed RAG source pipeline.
- Embeddings for new admin-managed chunks with deterministic local hashing or Bedrock Titan Text Embeddings V2.
- pgvector semantic retrieval for admin-managed chunks, with lexical fallback when vector search is unavailable.
- Admin-triggered embedding backfill/background indexing for missing or failed chunk embeddings.
- Persisted `rag_evidence` on program-fit analyses.
- Agent-stage metadata in async analysis job summaries.
- Deterministic verifier output with status, confidence, evidence count, warnings, blockers, and next-best actions.
- Deterministic Admission Intelligence aggregation over twelfth-student profiles and latest program-fit analyses.
- Deterministic Placement Intelligence aggregation over college-student profiles and latest readiness records.
- AIML/Cyber compatibility fields preserved during the Phase 2 transition.
- Admin override API for institution thresholds, priority skills, and counselor notes.

## Target LLM Provider

Phase 3 adds a provider abstraction for LLM inference. The current OpenAI-compatible provider remains supported, and AWS Bedrock can be selected with `LLM_PROVIDER=bedrock`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`. Seeded RAG is implemented in Phase 4. Deterministic agentic snapshot orchestration is implemented in Phase 5. DB-backed document RAG is implemented in Phase 6. Phase 9 adds Bedrock production setup documentation around the existing Converse API provider. Semantic RAG now exists for DB-backed text sources through PDF/DOCX upload parsing, chunk embeddings, pgvector migration support, lexical fallback, and admin-triggered backfill/background indexing. The institutional readiness wave adds RAG source review governance, freshness labels, and retrieval gating so pending/rejected/expired admin sources do not affect student guidance. Autonomous tool-calling agents and scheduled recurring indexing are still later phases.

The provider layer should support:

- Model ID configuration.
- Native Bedrock request format.
- Native Bedrock response parsing.
- Timeout settings.
- Retry policy.
- Structured output validation.
- Logging and usage metadata.

## Agentic Workflow

Phase 5 implements the first agentic workflow as a deterministic orchestration wrapper around existing modules.

The implemented snapshot records these stages where applicable:

1. Profile normalization.
2. Program fit or career pathway generation.
3. Placement risk analysis.
4. Internship readiness analysis.
5. Employability scoring for college students.
6. Company readiness for college students.
7. Role gap analysis for college students.
8. Verifier review.

The current workflow is deterministic orchestration with verifier checks. It is not yet an autonomous multi-agent tool-calling system.

## Phase 2 Configurable Institution Model

Phase 2 adds the configurable SAGE institution catalog, program-fit analysis contract, counselor expectation checks, and admin override API. The previous AIML/Cyber-specific fields remain available as compatibility fields during the transition.

## Phase 4 Seeded RAG Foundation

Phase 4 adds a deterministic seeded RAG baseline for pitch-ready evidence grounding:

- Curated SAGE/SIRT knowledge chunks in `backend/app/configs/rag_knowledge.json`.
- Lexical retrieval service with source type, program, and limit controls.
- Authenticated `/api/v1/rag/search` route for debugging and future UI surfaces.
- Retrieved evidence passed into the program-fit LLM prompt as bounded source title, source type, and excerpt fields.
- Retrieved evidence persisted as `career_analyses.rag_evidence`.
- Frontend Program Intelligence panel renders safe evidence snippets.

This phase does not include embeddings, pgvector, document upload, PDF indexing, or admin source approval workflow.

## Phase 5 Agentic Snapshot And Verifier

Phase 5 adds a verified student intelligence snapshot in `analysis_jobs.snapshot_summary`:

- `agent_stages` records stage name, label, status, source, output reference, and notes.
- `verifier` records approved, approved-with-warnings, or blocked status.
- Verifier output includes confidence, blockers, warnings, evidence count, and next-best actions.
- Blocked analysis snapshots are reported structurally instead of failing before verifier metadata exists.
- Frontend analysis pages show the agentic pipeline after a job completes.

## Phase 6 Document RAG Expansion

Phase 6 turns the seeded RAG baseline into an admin-managed institutional knowledge layer:

- `rag_document_sources` stores title, source type, tags, program IDs, status, content hash, creator, and timestamps.
- `rag_document_chunks` stores deterministic text chunks linked to source metadata.
- Admin-only APIs support create, list, and activate/deactivate workflows.
- Admin-only upload APIs parse PDF/DOCX knowledge files and create normal RAG sources.
- Normal authenticated RAG search merges seeded JSON chunks with active DB-backed chunks.
- Program-fit analysis uses `RAGService(self.db)` so admin-managed knowledge can ground future recommendations.
- The admin dashboard includes a compact knowledge panel for text source creation, PDF/DOCX upload, and lifecycle control.

The initial Phase 6 implementation was lexical and deterministic. The semantic RAG pass now extends the same `RAGDocumentService` and `RAGService` path with embeddings and pgvector-backed retrieval instead of creating a duplicate RAG module.

## Semantic RAG Pgvector Expansion

The semantic RAG pass adds:

- `EmbeddingProvider` abstraction with deterministic `hash` embeddings for local/test use and Bedrock Titan Text Embeddings V2 invocation for production use.
- Embedding storage on `rag_document_chunks`: vector, provider, model, dimensions, and update timestamp.
- Alembic revision `20260523_07_add_rag_pgvector_embeddings.py`, which installs the `vector` extension in the `extensions` schema and adds a 256-dimension pgvector column.
- `RAGDocumentService.semantic_search()`, which queries pgvector by cosine distance when available and falls back to in-memory embedding similarity for local/dev databases.
- `RAGService.search()`, which prefers semantic admin-document evidence and fills remaining slots with the existing lexical seeded/admin evidence path.
- `RAGDocumentService.reindex_embeddings()`, which backfills missing, pending, mismatched, or failed chunk embeddings in bounded batches.
- `RAGFileService`, which validates and extracts text from PDF/DOCX uploads before handing the text to `RAGDocumentService.create_source()`.
- `POST /api/v1/rag/admin/sources/upload`, which ingests a PDF/DOCX file plus source metadata using the same chunking and embedding path as manual text sources.
- The admin dashboard upload form, which reuses the same source metadata fields and calls the multipart upload endpoint.
- `POST /api/v1/rag/admin/embeddings/reindex`, which runs inline when `CELERY_TASK_ALWAYS_EAGER=true` and queues the `rag.reindex_embeddings` Celery task otherwise.

Production semantic RAG requires the migration to run successfully in the target Postgres/Supabase database and Bedrock model access if `RAG_EMBEDDING_PROVIDER=bedrock`. Existing admin chunks created before this pass can still be found lexically; operators should run the admin reindex endpoint after migration/provider validation to populate embeddings for old rows.

## Phase 7 Admission Intelligence Baseline

Phase 7 adds a deterministic admission intelligence layer. It does not call the LLM and does not introduce a CRM table. Instead, it derives institutional counseling signals from existing twelfth-student profiles, latest program-fit analyses, first-year roadmap fields, counselor summaries, expectation checks, and RAG evidence.

Implemented outputs:

- Admission metrics for total twelfth profiles, analyzed profiles, needs-analysis profiles, high-intent profiles, wrong-branch risk, and ready-for-counseling profiles.
- Lead cards sorted by priority.
- Counselor Copilot briefs with talking points, expectation checks, first-year actions, evidence titles, and follow-up questions.
- Lost-reason signals for missing analysis, low confidence, expectation mismatch, weak evidence, and unclear fit.

Later admission upgrades should add CRM imports, counselor assignment, admission status tracking, outbound communication, and conversion funnel attribution.

## Phase 8 Placement Intelligence Baseline

Phase 8 adds a deterministic placement intelligence layer. It does not call the LLM and does not introduce placement-drive tables. Instead, it derives institutional placement signals from existing college-student profiles, latest employability scores, placement risk records, company-fit matches, role-gap analyses, career-analysis skill gaps, and internship readiness records.

Implemented outputs:

- Placement metrics for college profiles, placement-ready students, training-needed students, high-risk students, company-ready students, evidence-complete students, and average employability.
- Skill Evidence Ledger scores combining projects, internships, certifications, resume quality, internship readiness, strengths, and skill gaps.
- AI Placement War Room cards sorted by urgency and employability need.
- Company-Specific Readiness Radar with ready, watch, and blocked counts per company.
- Training ROI signals with affected-student counts and expected readiness lift.
- Faculty Advisor notes for urgent and high-priority students.

Later placement upgrades should add recruiter-drive scheduling, placed/not-placed outcomes, company JD imports, faculty assignment workflows, notifications, and historical before/after training measurement.

## Phase 9 Bedrock Launch Readiness

Phase 9 documents the production Bedrock path without changing the AI service contract. The backend continues to use `BedrockConverseProvider` through `create_llm_provider(settings)`. Production operators configure `LLM_PROVIDER=bedrock`, `BEDROCK_REGION=ap-south-1`, and `BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0` or another sandbox-approved model or inference profile. `docs/BEDROCK_PRODUCTION_SETUP.md` documents the AWS credential chain, `bedrock:InvokeModel` permission, model access validation, quota checks, and logging rules that avoid raw student data.

## Deterministic Scoring

Use deterministic scoring for:

- Employability.
- Placement risk.
- Company fit.
- Internship readiness.
- Eligibility.
- Base branch/program fit from the configurable institution catalog and persisted program-fit fields.
- Admission intelligence status, priority, and lost-reason signals.
- Placement intelligence evidence score, priority, company readiness, faculty note focus, and training ROI signals.

LLM adjustments must be bounded and explainable.

## RAG Knowledge Sources

- SAGE/SIRT schools.
- Programs and branches.
- Syllabus and skill maps.
- Career pathways.
- Placement rules.
- Company criteria.
- Training calendars.
- Resume standards.
- Admission counseling FAQs.
- Industry role and salary notes.

## Evidence And Citations

Student-facing and admin-facing AI outputs should include evidence metadata:

- Source title.
- Source type.
- Retrieved excerpt.
- Confidence.
- Linked recommendation ID.

## Safety Rules

- Do not show raw chain-of-thought.
- Do not show unvalidated LLM output.
- Do not claim guaranteed salary or placement.
- Show realistic effort and preparation requirements.
- Mark weak evidence clearly.
- Fall back to deterministic or config-derived outputs when LLM generation fails.
