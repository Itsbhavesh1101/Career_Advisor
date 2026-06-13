import os

# Allow `pytest` to run without a local `.env`.
# SQLAlchemy `create_engine()` will not connect until first use.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/ai_career_intel_test",
)
os.environ.setdefault("AUTO_CREATE_TABLES", "false")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-with-at-least-32-chars")
os.environ.setdefault("DATA_RETENTION_ENABLED", "false")

