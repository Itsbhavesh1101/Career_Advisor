# Tech Stack

## Current Backend

- Python 3.11+ target from `backend/pyproject.toml`.
- FastAPI.
- Uvicorn.
- SQLAlchemy 2.0.
- Pydantic v2.
- Alembic.
- psycopg PostgreSQL driver.
- OpenAI Python SDK for the OpenAI-compatible provider.
- boto3 for the AWS Bedrock provider.
- python-dotenv.
- email-validator.
- Supabase Auth bearer-token verification through `httpx` remote verification or `python-jose` JWT-secret verification in local/test mode.
- passlib and bcrypt remain installed for retired local password-auth compatibility code only; backend login/signup now use Supabase Auth.
- python-multipart.
- slowapi rate limiting.
- httpx.
- pypdf and python-docx.
- Celery with Redis.

## Current Frontend

- Next.js App Router.
- React.
- TypeScript.
- Tailwind CSS.
- Recharts.
- Framer Motion.
- lucide-react.

## Current Database

- PostgreSQL-compatible schema.
- Supabase Postgres launch target.
- Alembic migrations for schema changes.

## Current AI Layer

- Phase 3 provider abstraction for LLM inference.
- OpenAI-compatible provider remains supported.
- AWS Bedrock can be selected with `LLM_PROVIDER=bedrock`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`.
- Seeded JSON RAG retrieval over curated SAGE/SIRT knowledge.
- DB-backed admin-managed RAG text/PDF/DOCX sources and chunks.
- Semantic pgvector-ready chunk embeddings and admin-triggered embedding reindexing.
- Persisted `rag_evidence` on career analyses.
- Deterministic agentic snapshot orchestration through `AnalysisSnapshotService`.
- Verifier output persisted in `analysis_jobs.snapshot_summary`.
- Strict Pydantic AI output schemas.
- JSON repair and normalization.
- LLM request budgets.
- Circuit breaker.
- Endpoint-specific rate limits.

## Target AI Provider

- AWS Bedrock native model APIs.
- Amazon native LLMs supported by the sandbox account.
- Provider abstraction that supports Bedrock and keeps OpenAI-compatible behavior working as the default fallback.
- Autonomous tool-calling agents remain a later phase.

## Target RAG Stack

- Implemented baseline: seeded JSON knowledge store, DB-backed admin text/PDF/DOCX sources, deterministic retrieval service, authenticated search API, persisted evidence snippets, admin knowledge panel, and frontend evidence display.
- Implemented semantic layer: Supabase vector or Postgres pgvector-ready chunk embeddings with lexical fallback and admin-triggered reindexing.
- Target governance: scheduled indexing, source review, source freshness tracking, and deeper admin-managed knowledge lifecycle.

## Target Hosting

- Frontend: Vercel.
- Backend: Google Cloud Run with the implemented `backend/Dockerfile`.
- Database: Supabase Postgres.
- LLM provider: AWS Bedrock.

## Current Deployment Artifacts

- `backend/Dockerfile` uses Python 3.12 slim, installs `backend/requirements.txt`, copies the FastAPI app and Alembic files, and starts Uvicorn on `${PORT:-8080}` for Cloud Run.
- `backend/.dockerignore` excludes local env files, virtualenvs, caches, storage, tests, and compiled Python artifacts.
- `deploy/cloud-run/backend.env.yaml.example` documents production environment variables without committed secrets.
- `deploy/cloud-run/deploy-backend.ps1` and `deploy/cloud-run/deploy-backend.sh` wrap `gcloud run deploy`.
- `docs/CLOUD_RUN_DEPLOYMENT.md` covers deployment, migration, smoke testing, rollback, Vercel configuration, and cost controls.
- `docs/BEDROCK_PRODUCTION_SETUP.md` covers Bedrock model configuration, IAM, credential strategy, and sandbox validation.

## Why This Stack Fits

- Low startup cost.
- Managed scaling.
- Strong Python backend ecosystem.
- Good institutional reliability story.
- Clear upgrade path from prototype to production.
