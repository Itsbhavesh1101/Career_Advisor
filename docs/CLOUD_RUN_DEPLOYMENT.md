# Cloud Run Deployment Runbook

## Target Architecture

Production launch path:

```text
Browser -> Vercel frontend -> Google Cloud Run backend -> Supabase Postgres
                                      |
                                      +-> AWS Bedrock Runtime
```

Cloud Run is used for the FastAPI backend because it can run a containerized service, scale down when idle, and scale up when traffic increases. Google documents that Cloud Run injects a `PORT` environment variable into the ingress container, so the backend Dockerfile starts Uvicorn on `${PORT:-8080}` and listens on `0.0.0.0`.

References:

- Cloud Run container runtime contract: https://cloud.google.com/run/docs/container-contract
- Cloud Run deploy from source: https://cloud.google.com/run/docs/deploying-source-code
- `gcloud run deploy` reference: https://cloud.google.com/sdk/gcloud/reference/run/deploy

## Prerequisites

- Google Cloud project with billing enabled.
- Cloud Run API enabled.
- Cloud Build API enabled.
- Artifact Registry enabled.
- `gcloud` CLI authenticated locally or Cloud Shell access.
- Supabase Postgres database created.
- Production database backup or restore point available.
- AWS Bedrock model access approved for the configured model.
- Bedrock runtime credentials available through the agreed production credential path.
- Vercel project connected to the frontend.

## Backend Environment Setup

Copy the example file and fill production values:

```powershell
copy deploy\cloud-run\backend.env.yaml.example deploy\cloud-run\backend.env.yaml
```

Required production values:

```yaml
ENVIRONMENT: production
DEBUG: "false"
DATABASE_URL: postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
AUTO_CREATE_TABLES: "false"
JWT_SECRET: use-a-strong-secret-through-secret-manager-or-approved-injection
SUPABASE_AUTH_ENABLED: "true"
SUPABASE_URL: https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY: __SET_SUPABASE_ANON_KEY__
SUPABASE_AUTH_VERIFY_MODE: remote
ADMIN_EMAILS: admin@sageuniversity.edu.in
CORS_ORIGINS: https://YOUR-VERCEL-APP.vercel.app
AUTH_COOKIE_SECURE: "true"
AUTH_COOKIE_SAMESITE: none
LLM_PROVIDER: bedrock
BEDROCK_REGION: ap-south-1
BEDROCK_MODEL_ID: apac.amazon.nova-lite-v1:0
PSYCHOMETRIC_SOFT_TIMEOUT_SECONDS: "8"
CELERY_TASK_ALWAYS_EAGER: "true"
```

Do not commit `deploy/cloud-run/backend.env.yaml`. Keep real secrets in Google Secret Manager or inject them through an approved deployment process.

For the first low-cost launch, keep `CELERY_TASK_ALWAYS_EAGER=true`. That avoids running a separate Redis and worker service. Move async jobs to Redis plus a worker service only when institutional traffic justifies the extra moving parts.

## Deploy Backend

PowerShell:

```powershell
.\deploy\cloud-run\deploy-backend.ps1 `
  -ProjectId "YOUR_GCP_PROJECT_ID" `
  -Region "asia-south1" `
  -Service "sage-career-backend"
```

On Windows, the PowerShell script prefers `gcloud.cmd` when available so the deploy does not depend on the `gcloud.ps1` execution-policy shim.

Cloud Shell or Linux:

```bash
PROJECT_ID="YOUR_GCP_PROJECT_ID" \
REGION="asia-south1" \
SERVICE="sage-career-backend" \
./deploy/cloud-run/deploy-backend.sh
```

Both scripts run:

```bash
gcloud run deploy sage-career-backend \
  --source backend \
  --region asia-south1 \
  --port 8080 \
  --env-vars-file deploy/cloud-run/backend.env.yaml \
  --allow-unauthenticated
```

The service is public because browser clients must reach the API. Application routes enforce Supabase bearer-token authentication and server-side admin authorization.

## Database Migration

Before shifting production traffic, run migrations against the Supabase database:

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME"
python -m alembic upgrade head
```

Migration safety checklist:

- Confirm the database URL points to the intended Supabase project.
- Create a Supabase backup or restore point before running migrations.
- Run migrations once per environment.
- Keep `AUTO_CREATE_TABLES=false` in production.

## Vercel Frontend

Set the frontend environment variable in Vercel:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR-CLOUD-RUN-SERVICE-URL
```

Redeploy the Vercel frontend after changing this value.

## Smoke Tests

Run these after backend deployment and frontend redeploy:

1. Open `https://YOUR-CLOUD-RUN-SERVICE-URL/health`.
2. Confirm response includes `{"status":"ok"}`.
3. Open the Vercel frontend URL.
4. Log in with an admin account.
5. Open the admin dashboard.
6. Confirm Admission Intelligence, Placement Intelligence, and RAG Knowledge panels load.
7. Create or open a test profile.
8. Run one analysis job with `LLM_PROVIDER=bedrock`.
9. Confirm the analysis completes or returns a controlled provider error without exposing raw secrets.
10. Confirm browser cookies are accepted with `AUTH_COOKIE_SECURE=true` and `AUTH_COOKIE_SAMESITE=none`.

## Rollback

Cloud Run rollback:

1. Open Cloud Run service revisions.
2. Select the previous healthy revision.
3. Route 100% traffic back to that revision.
4. Confirm `/health` and login still work.

CLI rollback option:

```powershell
gcloud run services update-traffic sage-career-backend `
  --region asia-south1 `
  --to-revisions PREVIOUS_REVISION=100
```

Database rollback:

- Prefer forward fixes for small application issues.
- Use Supabase point-in-time restore only when a migration or data change damages production state.
- Do not run destructive schema commands without a backup and a written recovery decision.

## Cost Controls

- Keep Cloud Run minimum instances at `0` for launch.
- Keep request and LLM daily limits enabled.
- Keep Bedrock model IDs explicit.
- Keep data retention enabled.
- Add minimum instances only if cold starts become a real demo or operational problem.
