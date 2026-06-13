# Deployment Strategy

## Target Production Story

SAGE AI Career Navigator should run as a low-cost, scalable, and reliable institutional platform:

- Frontend on Vercel.
- Backend on Google Cloud Run.
- Database on Supabase Postgres.
- LLM inference through the Phase 3 provider abstraction, with OpenAI-compatible fallback support and AWS Bedrock selectable for production.
- Seeded and admin-managed text/PDF/DOCX RAG evidence from the backend knowledge store, with pgvector semantic retrieval available for embedded admin chunks through Supabase Postgres after migrations are applied.

Phase 9 launch artifacts are now implemented:

- `backend/Dockerfile` for Cloud Run-compatible FastAPI deployment.
- `backend/.dockerignore` to keep secrets, local state, and tests out of the image.
- `deploy/cloud-run/backend.env.yaml.example` for production environment setup.
- `deploy/cloud-run/deploy-backend.ps1` and `deploy/cloud-run/deploy-backend.sh` for repeatable backend deployment.
- `docs/CLOUD_RUN_DEPLOYMENT.md` for deployment, migration, smoke-test, rollback, and cost-control steps.
- `docs/BEDROCK_PRODUCTION_SETUP.md` for Bedrock model, IAM, credential, and governance setup.

Live Cloud Run deployment is still a manual operational step. This repository now contains the artifacts needed to perform it safely.

## Why Google Cloud Run

- Managed container hosting.
- Scales down when idle.
- Scales up under load.
- Good FastAPI deployment fit.
- Clear path from prototype to production.
- Avoids dependence on temporary trial hosting.

## Why Supabase Postgres

- PostgreSQL compatibility.
- Managed database.
- Free or low-cost launch path.
- Future pgvector support for RAG.

## Why AWS Bedrock

- Managed access to native Amazon LLMs.
- Better institutional production story than ad hoc API keys.
- Sandbox-account compatibility.
- Clear path for provider governance and model configuration.

## Environment Variables

Backend:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET=replace-with-strong-secret
SUPABASE_AUTH_ENABLED=true
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_AUTH_VERIFY_MODE=remote
ADMIN_EMAILS=admin@example.com
CORS_ORIGINS=https://your-vercel-app.vercel.app
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
AUTO_CREATE_TABLES=false
AWS_REGION=ap-south-1
LLM_PROVIDER=bedrock
BEDROCK_REGION=ap-south-1
BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0
RAG_VECTOR_SEARCH_ENABLED=true
RAG_EMBEDDING_PROVIDER=bedrock
RAG_EMBEDDING_DIMENSIONS=256
RAG_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
RAG_EMBEDDING_BEDROCK_REGION=ap-south-1
```

Bedrock uses AWS runtime credential resolution from Cloud Run or the local AWS environment. Do not store AWS secrets in `.env` files.

Frontend:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-cloud-run-service-url
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Launch Readiness Checklist

- Backend tests pass.
- Frontend build passes.
- Alembic migrations applied.
- Production CORS configured.
- Supabase Auth configured in backend and frontend deployments.
- Supabase database backup approach documented.
- Bedrock runtime credentials available through the Cloud Run service environment or attached identity.
- Supabase/Postgres `vector` extension migration applied for semantic RAG.
- Bedrock Titan embedding model access validated when `RAG_EMBEDDING_PROVIDER=bedrock`.
- RAG embedding reindex run once after migration through `POST /api/v1/rag/admin/embeddings/reindex`.
- Admin PDF/DOCX knowledge upload smoke-tested through `POST /api/v1/rag/admin/sources/upload`.
- Cloud Run service health check passes.
- Vercel frontend points to Cloud Run backend.
- Admin account configured.

## Migration Strategy

1. Keep current local development flow.
2. Use the implemented backend container deployment artifacts.
3. Deploy backend to Cloud Run staging service.
4. Point frontend staging environment to Cloud Run.
5. Run smoke tests.
6. Apply production database migrations.
7. Promote Cloud Run service for launch demo.

## Operational Risks

- LLM quota or model availability: mitigate with provider abstraction, retries, and fallback messages.
- Database migration failure: mitigate with backup and Alembic runbook.
- Cross-domain cookie issues: mitigate with explicit CORS and cookie settings.
- Cold start latency: mitigate with Cloud Run minimum instances only if needed.
- RAG data quality: mitigate with curated seeded knowledge, admin source governance, PDF/DOCX text extraction review, and embedding reindexing for old or failed admin chunks.

Seeded RAG, admin-managed text/PDF/DOCX RAG, semantic vector retrieval for embedded admin chunks, and admin-triggered embedding reindexing are implemented. Scheduled recurring indexing, source review workflows, and autonomous multi-agent orchestration remain later phases.
