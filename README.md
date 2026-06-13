# SAGE AI Career Navigator

SAGE AI Career Navigator is a working career and placement intelligence platform prototype for SAGE/SIRT, with a target product vision to become an internal Student Success OS connecting admission counseling, configurable program decision support, student skill development, resume intelligence, placement readiness, and institutional outcome analytics.

The current platform already supports profile intake, AI-assisted analysis, resume review, readiness scoring, and admin dashboards. Phase 2 adds the configurable SAGE institution catalog, program-fit analysis contract, counselor expectation checks, and admin override API. Phase 3 adds the LLM provider abstraction. The OpenAI-compatible provider remains supported, and AWS Bedrock can be selected with `LLM_PROVIDER=bedrock`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`. Phase 4 adds seeded RAG retrieval over curated SAGE/SIRT knowledge, persists retrieved evidence on program-fit analyses, and shows evidence snippets in the frontend. Phase 5 adds an agentic analysis snapshot over the existing modules: async job summaries now record agent stages, verifier status, confidence, evidence count, warnings, and next-best actions. Phase 6 adds DB-backed document RAG: admins can add text knowledge sources or upload PDF/DOCX knowledge files, activate or deactivate sources, and merge those chunks with seeded evidence during retrieval. The semantic RAG pass now generates embeddings for admin-managed chunks, adds a pgvector migration, lets retrieval prefer semantic DB results while falling back to lexical evidence, and includes admin-triggered backfill/background indexing for missing or failed embeddings. Phase 7 adds the Admission Intelligence baseline: admin-only metrics, high-intent and wrong-branch-risk lead cards, Counselor Copilot briefs, and lost-reason signals derived from existing twelfth-student profiles and program-fit analyses. Phase 8 adds the Placement Intelligence baseline: admin-only Skill Evidence Ledger, Company-Specific Readiness Radar, AI Placement War Room, Faculty Advisor notes, Outcome Simulation proxy, and Training ROI signals derived from existing college-student readiness records. Phase 9 adds launch-readiness artifacts: a Cloud Run backend Dockerfile, deploy scripts, env template, deployment runbook, and Bedrock production setup guide. The previous AIML/Cyber-specific fields remain available as compatibility fields during the transition.

The production roadmap extends it into an institution-specific intelligence platform designed around SAGE programs, student evidence, placement rules, agentic AI, RAG, and deterministic readiness scoring.

## Product Vision

The platform helps SAGE/SIRT answer one complete lifecycle question:

> How do we guide a student from the right admission decision to the right skill roadmap and the right placement outcome?

## Target Wow-Factor Pillars

These pillars are the target product differentiators for upcoming implementation phases.

### Admission Intelligence Command Center

- Expectation Reality Check.
- Counselor Copilot.
- Admission Conversion Intelligence.
- Lost Admission Reason Analyzer.
- High-intent undecided student tracking.
- First 100-day roadmap after admission.

### Placement Intelligence Command Center

- Student Skill Evidence Ledger.
- Company-Specific Readiness Radar.
- AI Placement War Room.
- Personal AI Faculty Advisor.
- Outcome Simulation.
- Training ROI Engine.

## Current Capabilities

- Student profile intake.
- Configurable program-fit and career analysis.
- Employability score.
- Placement risk.
- Resume AI scanner.
- Company fit predictor.
- Role-based skill gap analysis.
- AI career chat assistant.
- Internship readiness.
- Placement opportunity board, student interest/apply tracking, and placement-cell application review.
- Psychometric quiz.
- Cohort training recommendations.
- Admin placement-cell dashboard.
- Admin Admission Intelligence Command Center baseline.
- Admin Placement Intelligence Command Center baseline.
- Cloud Run backend container and launch runbooks.
- Async AI analysis jobs.
- SAGE institution catalog and admin override API.
- Counselor expectation reality checks in the program-fit contract.
- Seeded, admin-managed, and semantic pgvector-backed RAG evidence for program-fit analysis.
- Admin dashboard PDF/DOCX RAG knowledge upload and ingestion.
- Admin-triggered RAG embedding reindex/backfill for missing or failed chunk embeddings.
- Agentic analysis snapshot with verifier status and stage metadata.
- Counselor Copilot briefs and lost-admission reason signals for twelfth-student profiles.
- Skill Evidence Ledger, Company-Specific Readiness Radar, Training ROI signals, and Faculty Advisor notes for college-student placement planning.

## Target Architecture

- Frontend: Next.js, TypeScript, Tailwind, Recharts.
- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic.
- Auth: Supabase Auth bearer tokens with backend user mapping and server-side admin role checks.
- Database: Supabase PostgreSQL.
- AI provider: OpenAI-compatible by default, with AWS Bedrock selectable through the Phase 3 provider abstraction.
- RAG: seeded JSON retrieval plus DB-backed admin text sources are implemented; admin chunks now store embeddings and production Postgres/Supabase can use pgvector semantic retrieval with lexical fallback.
- Orchestration: deterministic agent-stage snapshot and verifier output are implemented around existing modules.
- Backend hosting target: Google Cloud Run.
- Backend deployment artifacts: `backend/Dockerfile`, `deploy/cloud-run/backend.env.yaml.example`, and deploy scripts.
- Frontend hosting: Vercel.

## Local Backend Setup

```powershell
cd backend
copy .env.example .env
```

Update:

```env
DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB"
JWT_SECRET="replace-with-at-least-32-characters"
SUPABASE_AUTH_ENABLED="true"
SUPABASE_URL="https://YOUR-PROJECT.supabase.co"
SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_KEY"
SUPABASE_AUTH_VERIFY_MODE="remote"
OPENAI_API_KEY=""
LLM_PROVIDER="openai"
BEDROCK_REGION="ap-south-1"
BEDROCK_MODEL_ID="apac.amazon.nova-lite-v1:0"
RAG_VECTOR_SEARCH_ENABLED="true"
RAG_EMBEDDING_PROVIDER="hash"
RAG_EMBEDDING_DIMENSIONS="256"
RAG_EMBEDDING_MODEL="amazon.titan-embed-text-v2:0"
ADMIN_EMAILS="admin@example.com"
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

Supabase is the only active login/signup path. Backend password login/register endpoints are retired and protected APIs expect `Authorization: Bearer <Supabase access token>`.

OpenAI-compatible inference remains the default local fallback. To use Bedrock, set `LLM_PROVIDER=bedrock`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`; AWS credentials are resolved from the runtime environment rather than stored in `.env`.

For local RAG development, `RAG_EMBEDDING_PROVIDER=hash` keeps embeddings deterministic and offline. For production semantic RAG, set `RAG_EMBEDDING_PROVIDER=bedrock`, run `uv run python -m alembic upgrade head`, and verify the target Postgres/Supabase database can install the `vector` extension in the `extensions` schema. Admins can upload PDF/DOCX knowledge from the admin dashboard or through `POST /api/v1/rag/admin/sources/upload`, and trigger chunk reindexing through `POST /api/v1/rag/admin/embeddings/reindex`; local eager mode runs reindexing inline, while non-eager Celery mode queues `rag.reindex_embeddings`.

Install:

```powershell
cd backend
uv sync
```

Apply migrations:

```powershell
cd backend
uv run python -m alembic upgrade head
```

Run API:

```powershell
cd backend
uv run python -m uvicorn main:app --reload
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Local Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Verification

Backend:

```powershell
cd backend
uv run python -m pytest
uv run python -m compileall app tests main.py
```

Frontend:

```powershell
cd frontend
npm run build
```

Known quality note:

```powershell
cd frontend
npx biome check app components lib proxy.ts
```

The current codebase has existing Biome formatting/import diagnostics. Keep that cleanup separate from feature implementation unless explicitly assigned.

## Documentation

Available now:

- `SYSTEM_AUDIT.md`
- `docs/FEATURE_SPEC.md`
- `docs/TECH_STACK.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/AI_ML_RAG_DESIGN.md`
- `docs/DEPLOYMENT_STRATEGY.md`
- `docs/CLOUD_RUN_DEPLOYMENT.md`
- `docs/BEDROCK_PRODUCTION_SETUP.md`
- `docs/2026-05-19-sage-ai-career-navigator-design.md`
- `docs/2026-05-23-rag-embedding-backfill-indexing.md`
- `docs/2026-05-23-rag-pdf-ingestion.md`

## Implementation Roadmap

1. Foundation and documentation.
2. Configurable SAGE institution model. Implemented: seeded SAGE catalog, generic program-fit fields, counselor expectation checks, admin overrides, and AIML/Cyber compatibility fields.
3. LLM provider abstraction. Implemented: OpenAI-compatible fallback plus selectable AWS Bedrock provider settings.
4. Seeded institution-specific RAG. Implemented: curated SAGE/SIRT knowledge base, authenticated search API, persisted `rag_evidence`, and frontend evidence snippets.
5. Agentic analysis orchestrator and verifier agent. Implemented: stage metadata, verifier result, confidence, warnings, blocked snapshot reporting, and frontend pipeline panel.
6. Document RAG expansion. Implemented: DB-backed text knowledge sources, PDF/DOCX knowledge upload and parsing, admin activate/deactivate flow, merged seeded plus admin retrieval, admin knowledge panel, embedding generation for new admin chunks, pgvector migration, semantic retrieval preference with lexical fallback, and admin-triggered embedding backfill/background indexing. Remaining upgrades: source review and scheduled recurring indexing.
7. Admission Intelligence Command Center. Implemented baseline: deterministic admin dashboard from existing twelfth-student profiles and program-fit analyses, with metrics, high-intent and wrong-branch-risk lead cards, Counselor Copilot briefs, and lost-reason signals. Remaining upgrades: CRM imports, counselor assignment, admission status tracking, outbound communication, and conversion funnel attribution.
8. Placement Intelligence Command Center. Implemented baseline: deterministic admin dashboard from existing college-student profiles and readiness records, with Skill Evidence Ledger, Company-Specific Readiness Radar, AI Placement War Room, Faculty Advisor notes, Outcome Simulation proxy, and Training ROI signals. Implemented placement operations: admin opportunity board, CSV exports, guided eligibility controls, student matched opportunities, student interest/apply notes, placement-cell review notes, pipeline statuses, next-step instructions, and package/vacancy/contact/stage metadata. Remaining upgrades: recruiter/import integrations, interview calendar automation, offer-document workflows, notifications, faculty assignment workflows, and historical before/after training measurement.
9. Cloud Run deployment artifacts and Bedrock production setup. Implemented: backend Dockerfile, dockerignore, Cloud Run env template, PowerShell and Cloud Shell deploy scripts, migration/smoke-test/rollback runbook, and Bedrock production setup guide. Remaining action: perform the live deployment with real project IDs, Supabase URL, JWT secret, Vercel URL, and approved AWS credential path.
