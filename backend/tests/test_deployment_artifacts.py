from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def test_backend_dockerfile_is_cloud_run_compatible() -> None:
    dockerfile = (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "COPY app ./app" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile
    assert "EXPOSE 8080" in dockerfile
    assert "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}" in dockerfile


def test_backend_dockerignore_excludes_local_state_and_secrets() -> None:
    dockerignore = (BACKEND_ROOT / ".dockerignore").read_text(encoding="utf-8")

    required_patterns = [
        ".env",
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        "storage/",
        "*.pyc",
        "tests/",
    ]
    for pattern in required_patterns:
        assert pattern in dockerignore


def test_cloud_run_env_template_is_non_secret_and_complete() -> None:
    env_template = (
        REPO_ROOT / "deploy" / "cloud-run" / "backend.env.yaml.example"
    ).read_text(encoding="utf-8")

    required_keys = [
        "ENVIRONMENT: production",
        'DEBUG: "false"',
        'AUTO_CREATE_TABLES: "false"',
        "JWT_SECRET:",
        "LLM_PROVIDER: bedrock",
        "BEDROCK_REGION: ap-south-1",
        "BEDROCK_MODEL_ID: apac.amazon.nova-lite-v1:0",
        'PSYCHOMETRIC_SOFT_TIMEOUT_SECONDS: "8"',
        'AUTH_COOKIE_SECURE: "true"',
        "AUTH_COOKIE_SAMESITE: none",
        'CELERY_TASK_ALWAYS_EAGER: "true"',
    ]
    for key in required_keys:
        assert key in env_template

    forbidden_values = [
        "replace-with-at-least-32-characters",
        "postgres:postgres",
        "AKIA",
        "OPENAI_API_KEY:",
    ]
    for value in forbidden_values:
        assert value not in env_template


def test_cloud_run_deploy_scripts_use_backend_source_and_env_template() -> None:
    powershell = (
        REPO_ROOT / "deploy" / "cloud-run" / "deploy-backend.ps1"
    ).read_text(encoding="utf-8")
    shell = (
        REPO_ROOT / "deploy" / "cloud-run" / "deploy-backend.sh"
    ).read_text(encoding="utf-8")

    for script in (powershell, shell):
        assert "sage-career-backend" in script
        assert "--source" in script
        assert "backend" in script
        assert "--env-vars-file" in script
        assert "backend.env.yaml" in script
        assert "JWT_SECRET" in script
        assert "--allow-unauthenticated" in script
        assert "--port 8080" in script


def test_launch_runbooks_cover_migration_bedrock_and_smoke_tests() -> None:
    cloud_run = (REPO_ROOT / "docs" / "CLOUD_RUN_DEPLOYMENT.md").read_text(
        encoding="utf-8"
    )
    bedrock = (REPO_ROOT / "docs" / "BEDROCK_PRODUCTION_SETUP.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "gcloud run deploy",
        "alembic upgrade head",
        "/health",
        "NEXT_PUBLIC_API_BASE_URL",
        "rollback",
    ]:
        assert phrase in cloud_run

    for phrase in [
        "bedrock:InvokeModel",
        "Converse API",
        "BEDROCK_MODEL_ID",
        "ap-south-1",
        "AWS credential chain",
    ]:
        assert phrase in bedrock
