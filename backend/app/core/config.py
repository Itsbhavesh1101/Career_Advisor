from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator


def _getenv(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value if value else default


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


class Settings(BaseModel):
    app_name: str = "AI Career Intelligence Agent"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = False
    institution_mode: Literal["sage", "generic"] = "sage"

    database_url: str
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_connect_timeout_seconds: int = 5

    auto_create_tables: bool = False
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = 30
    openai_max_retries: int = 2
    llm_provider: Literal["openai", "bedrock"] = "openai"
    bedrock_region: str | None = None
    bedrock_model_id: str = "apac.amazon.nova-lite-v1:0"
    bedrock_timeout_seconds: int = 45
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "ai-career-advisor"
    jwt_audience: str = "ai-career-advisor-web"
    access_token_expire_minutes: int = 60
    auth_cookie_name: str = "access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_cookie_domain: str | None = None
    auth_rate_limit: str = "10/minute"
    auth_me_rate_limit: str = "120/minute"
    supabase_auth_enabled: bool = False
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_auth_verify_mode: Literal["remote", "jwt_secret"] = "remote"
    supabase_jwt_secret: str | None = None
    analysis_rate_limit: str = "20/minute"
    chat_rate_limit: str = "30/minute"
    quiz_start_rate_limit: str = "10/minute"
    quiz_answer_rate_limit: str = "60/minute"

    data_retention_enabled: bool = True
    data_retention_days: int = 90
    data_retention_keep_latest_per_profile: int = 3
    data_retention_cleanup_interval_minutes: int = 720
    data_retention_run_on_startup: bool = True

    llm_daily_request_limit: int = 300
    llm_user_daily_request_limit: int = 120
    llm_prompt_max_chars: int = 12000
    llm_max_output_tokens: int = 1000
    llm_circuit_breaker_threshold: int = 5
    llm_circuit_breaker_reset_seconds: int = 120
    llm_analysis_endpoint_daily_limit: int = 120
    llm_chat_endpoint_daily_limit: int = 600
    llm_industry_endpoint_daily_limit: int = 120
    llm_quiz_endpoint_daily_limit: int = 240
    llm_program_fit_endpoint_daily_limit: int = 120

    rag_vector_search_enabled: bool = True
    rag_embedding_provider: Literal["hash", "bedrock"] = "hash"
    rag_embedding_dimensions: int = 256
    rag_embedding_model: str = "amazon.titan-embed-text-v2:0"
    rag_embedding_bedrock_region: str | None = None
    rag_embedding_timeout_seconds: int = 20
    rag_semantic_min_score: float = 0.0

    psychometric_quiz_enabled: bool = True
    psychometric_min_questions: int = 8
    psychometric_max_questions: int = 15
    psychometric_confidence_threshold: float = 0.75
    psychometric_breaker_threshold: int = 3
    psychometric_max_tokens_per_session: int = 3000
    psychometric_soft_timeout_seconds: int = 2
    psychometric_schema_version: str = "v1"
    psychometric_prompt_version: str = "v1"

    resume_url_allow_http: bool = False
    resume_url_validate_dns: bool = True
    resume_url_max_length: int = 2048
    resume_fetch_timeout_seconds: int = 12
    resume_fetch_max_bytes: int = 5 * 1024 * 1024

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    admin_emails: list[str] = []
    cors_origins: list[str] = []

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value.lower().startswith("postgresql"):
            raise ValueError("DATABASE_URL must start with 'postgresql'.")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters.")
        return value

    @field_validator(
        "data_retention_days",
        "data_retention_keep_latest_per_profile",
        "data_retention_cleanup_interval_minutes",
        "openai_timeout_seconds",
        "openai_max_retries",
        "bedrock_timeout_seconds",
        "llm_daily_request_limit",
        "llm_user_daily_request_limit",
        "llm_prompt_max_chars",
        "llm_max_output_tokens",
        "llm_circuit_breaker_threshold",
        "llm_circuit_breaker_reset_seconds",
        "llm_analysis_endpoint_daily_limit",
        "llm_chat_endpoint_daily_limit",
        "llm_industry_endpoint_daily_limit",
        "llm_quiz_endpoint_daily_limit",
        "llm_program_fit_endpoint_daily_limit",
        "rag_embedding_dimensions",
        "rag_embedding_timeout_seconds",
        "psychometric_min_questions",
        "psychometric_max_questions",
        "psychometric_breaker_threshold",
        "psychometric_max_tokens_per_session",
        "psychometric_soft_timeout_seconds",
        "resume_url_max_length",
        "resume_fetch_timeout_seconds",
        "resume_fetch_max_bytes",
        "db_connect_timeout_seconds",
    )
    @classmethod
    def _validate_positive_numbers(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Numeric setting values must be >= 1.")
        return value

    @field_validator("psychometric_confidence_threshold")
    @classmethod
    def _validate_confidence_threshold(cls, value: float) -> float:
        if value <= 0 or value > 1:
            raise ValueError("psychometric_confidence_threshold must be within (0, 1].")
        return value

    @field_validator("rag_semantic_min_score")
    @classmethod
    def _validate_rag_semantic_min_score(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("rag_semantic_min_score must be within [0, 1].")
        return value

    @field_validator("psychometric_max_questions")
    @classmethod
    def _validate_psychometric_max_questions(cls, value: int, info) -> int:  # type: ignore[override]
        min_questions = info.data.get("psychometric_min_questions")
        if isinstance(min_questions, int) and value < min_questions:
            raise ValueError("psychometric_max_questions must be >= psychometric_min_questions.")
        return value

    @model_validator(mode="after")
    def _validate_llm_provider_settings(self) -> "Settings":
        if self.llm_provider == "bedrock" and not self.bedrock_region:
            raise ValueError(
                "BEDROCK_REGION or AWS_REGION is required when LLM_PROVIDER=bedrock."
            )
        if self.supabase_auth_enabled:
            if not self.supabase_url:
                raise ValueError("SUPABASE_URL is required when SUPABASE_AUTH_ENABLED=true.")
            if self.supabase_auth_verify_mode == "remote" and not self.supabase_anon_key:
                raise ValueError(
                    "SUPABASE_ANON_KEY is required for remote Supabase Auth verification."
                )
            if self.supabase_auth_verify_mode == "jwt_secret" and not self.supabase_jwt_secret:
                raise ValueError(
                    "SUPABASE_JWT_SECRET is required for jwt_secret Supabase Auth verification."
                )
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)

        database_url = _getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required (see backend/.env.example).")

        jwt_secret = _getenv("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET is required and must be at least 32 characters.")

        environment = _getenv("ENVIRONMENT", "local") or "local"
        debug = _parse_bool(_getenv("DEBUG"), default=False)
        if environment == "production" and debug:
            raise RuntimeError("DEBUG must be false in production.")

        auto_create_tables = _parse_bool(_getenv("AUTO_CREATE_TABLES"), default=False)
        if environment != "local" and auto_create_tables:
            raise RuntimeError("AUTO_CREATE_TABLES must be false outside local environment.")

        default_cookie_secure = environment != "local"
        default_cookie_samesite = "strict"

        return cls(
            app_name=_getenv("APP_NAME", "AI Career Intelligence Agent") or "AI Career Intelligence Agent",
            environment=environment,
            debug=debug,
            institution_mode=(
                _getenv("INSTITUTION_MODE", "sage") or "sage"
            ).lower(),
            database_url=database_url,
            db_echo=_parse_bool(_getenv("DB_ECHO"), default=False),
            db_pool_size=int(_getenv("DB_POOL_SIZE", "5") or "5"),
            db_max_overflow=int(_getenv("DB_MAX_OVERFLOW", "10") or "10"),
            db_connect_timeout_seconds=int(
                _getenv("DB_CONNECT_TIMEOUT_SECONDS", "5") or "5"
            ),
            auto_create_tables=auto_create_tables,
            openai_api_key=_getenv("OPENAI_API_KEY"),
            openai_base_url=_getenv("OPENAI_BASE_URL"),
            openai_model=_getenv("OPENAI_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini",
            openai_timeout_seconds=int(_getenv("OPENAI_TIMEOUT_SECONDS", "30") or "30"),
            openai_max_retries=int(_getenv("OPENAI_MAX_RETRIES", "2") or "2"),
            llm_provider=(_getenv("LLM_PROVIDER", "openai") or "openai").lower(),
            bedrock_region=_getenv("BEDROCK_REGION") or _getenv("AWS_REGION") or None,
            bedrock_model_id=(
                _getenv("BEDROCK_MODEL_ID", "apac.amazon.nova-lite-v1:0")
                or "apac.amazon.nova-lite-v1:0"
            ),
            bedrock_timeout_seconds=int(
                _getenv("BEDROCK_TIMEOUT_SECONDS", "45") or "45"
            ),
            jwt_secret=jwt_secret,
            jwt_algorithm=_getenv("JWT_ALGORITHM", "HS256") or "HS256",
            jwt_issuer=_getenv("JWT_ISSUER", "ai-career-advisor") or "ai-career-advisor",
            jwt_audience=_getenv("JWT_AUDIENCE", "ai-career-advisor-web")
            or "ai-career-advisor-web",
            access_token_expire_minutes=int(
                _getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60") or "60"
            ),
            auth_cookie_name=_getenv("AUTH_COOKIE_NAME", "access_token") or "access_token",
            auth_cookie_secure=_parse_bool(
                _getenv("AUTH_COOKIE_SECURE"), default=default_cookie_secure
            ),
            auth_cookie_samesite=(
                _getenv("AUTH_COOKIE_SAMESITE", default_cookie_samesite)
                or default_cookie_samesite
            ).lower(),
            auth_cookie_domain=_getenv("AUTH_COOKIE_DOMAIN") or None,
            auth_rate_limit=_getenv("AUTH_RATE_LIMIT", "10/minute") or "10/minute",
            auth_me_rate_limit=_getenv("AUTH_ME_RATE_LIMIT", "120/minute")
            or "120/minute",
            supabase_auth_enabled=_parse_bool(
                _getenv("SUPABASE_AUTH_ENABLED"), default=False
            ),
            supabase_url=(_getenv("SUPABASE_URL") or "").rstrip("/") or None,
            supabase_anon_key=_getenv("SUPABASE_ANON_KEY") or None,
            supabase_auth_verify_mode=(
                _getenv("SUPABASE_AUTH_VERIFY_MODE", "remote") or "remote"
            ).lower(),
            supabase_jwt_secret=_getenv("SUPABASE_JWT_SECRET") or None,
            analysis_rate_limit=_getenv("ANALYSIS_RATE_LIMIT", "20/minute")
            or "20/minute",
            chat_rate_limit=_getenv("CHAT_RATE_LIMIT", "30/minute") or "30/minute",
            quiz_start_rate_limit=_getenv("QUIZ_START_RATE_LIMIT", "10/minute")
            or "10/minute",
            quiz_answer_rate_limit=_getenv("QUIZ_ANSWER_RATE_LIMIT", "60/minute")
            or "60/minute",
            data_retention_enabled=_parse_bool(
                _getenv("DATA_RETENTION_ENABLED"), default=True
            ),
            data_retention_days=int(_getenv("DATA_RETENTION_DAYS", "90") or "90"),
            data_retention_keep_latest_per_profile=int(
                _getenv("DATA_RETENTION_KEEP_LATEST_PER_PROFILE", "3") or "3"
            ),
            data_retention_cleanup_interval_minutes=int(
                _getenv("DATA_RETENTION_CLEANUP_INTERVAL_MINUTES", "720") or "720"
            ),
            data_retention_run_on_startup=_parse_bool(
                _getenv("DATA_RETENTION_RUN_ON_STARTUP"), default=True
            ),
            llm_daily_request_limit=int(
                _getenv("LLM_DAILY_REQUEST_LIMIT", "300") or "300"
            ),
            llm_user_daily_request_limit=int(
                _getenv("LLM_USER_DAILY_REQUEST_LIMIT", "120") or "120"
            ),
            llm_prompt_max_chars=int(
                _getenv("LLM_PROMPT_MAX_CHARS", "12000") or "12000"
            ),
            llm_max_output_tokens=int(
                _getenv("LLM_MAX_OUTPUT_TOKENS", "1000") or "1000"
            ),
            llm_circuit_breaker_threshold=int(
                _getenv("LLM_CIRCUIT_BREAKER_THRESHOLD", "5") or "5"
            ),
            llm_circuit_breaker_reset_seconds=int(
                _getenv("LLM_CIRCUIT_BREAKER_RESET_SECONDS", "120") or "120"
            ),
            llm_analysis_endpoint_daily_limit=int(
                _getenv("LLM_ANALYSIS_ENDPOINT_DAILY_LIMIT", "120") or "120"
            ),
            llm_chat_endpoint_daily_limit=int(
                _getenv("LLM_CHAT_ENDPOINT_DAILY_LIMIT", "600") or "600"
            ),
            llm_industry_endpoint_daily_limit=int(
                _getenv("LLM_INDUSTRY_ENDPOINT_DAILY_LIMIT", "120") or "120"
            ),
            llm_quiz_endpoint_daily_limit=int(
                _getenv("LLM_QUIZ_ENDPOINT_DAILY_LIMIT", "240") or "240"
            ),
            llm_program_fit_endpoint_daily_limit=int(
                _getenv("LLM_PROGRAM_FIT_ENDPOINT_DAILY_LIMIT", "120") or "120"
            ),
            rag_vector_search_enabled=_parse_bool(
                _getenv("RAG_VECTOR_SEARCH_ENABLED"), default=True
            ),
            rag_embedding_provider=(
                _getenv("RAG_EMBEDDING_PROVIDER", "hash") or "hash"
            ).lower(),
            rag_embedding_dimensions=int(
                _getenv("RAG_EMBEDDING_DIMENSIONS", "256") or "256"
            ),
            rag_embedding_model=(
                _getenv("RAG_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
                or "amazon.titan-embed-text-v2:0"
            ),
            rag_embedding_bedrock_region=_getenv("RAG_EMBEDDING_BEDROCK_REGION")
            or None,
            rag_embedding_timeout_seconds=int(
                _getenv("RAG_EMBEDDING_TIMEOUT_SECONDS", "20") or "20"
            ),
            rag_semantic_min_score=float(
                _getenv("RAG_SEMANTIC_MIN_SCORE", "0") or "0"
            ),
            psychometric_quiz_enabled=_parse_bool(
                _getenv("PSYCHOMETRIC_QUIZ_ENABLED"), default=True
            ),
            psychometric_min_questions=int(
                _getenv("PSYCHOMETRIC_MIN_QUESTIONS", "8") or "8"
            ),
            psychometric_max_questions=int(
                _getenv("PSYCHOMETRIC_MAX_QUESTIONS", "15") or "15"
            ),
            psychometric_confidence_threshold=float(
                _getenv("PSYCHOMETRIC_CONFIDENCE_THRESHOLD", "0.75") or "0.75"
            ),
            psychometric_breaker_threshold=int(
                _getenv("PSYCHOMETRIC_BREAKER_THRESHOLD", "3") or "3"
            ),
            psychometric_max_tokens_per_session=int(
                _getenv("PSYCHOMETRIC_MAX_TOKENS_PER_SESSION", "3000") or "3000"
            ),
            psychometric_soft_timeout_seconds=int(
                _getenv("PSYCHOMETRIC_SOFT_TIMEOUT_SECONDS", "2") or "2"
            ),
            psychometric_schema_version=_getenv("PSYCHOMETRIC_SCHEMA_VERSION", "v1") or "v1",
            psychometric_prompt_version=_getenv("PSYCHOMETRIC_PROMPT_VERSION", "v1") or "v1",
            resume_url_allow_http=_parse_bool(
                _getenv("RESUME_URL_ALLOW_HTTP"), default=False
            ),
            resume_url_validate_dns=_parse_bool(
                _getenv("RESUME_URL_VALIDATE_DNS"), default=True
            ),
            resume_url_max_length=int(
                _getenv("RESUME_URL_MAX_LENGTH", "2048") or "2048"
            ),
            resume_fetch_timeout_seconds=int(
                _getenv("RESUME_FETCH_TIMEOUT_SECONDS", "12") or "12"
            ),
            resume_fetch_max_bytes=int(
                _getenv("RESUME_FETCH_MAX_BYTES", str(5 * 1024 * 1024)) or str(5 * 1024 * 1024)
            ),
            celery_broker_url=_getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
            or "redis://localhost:6379/0",
            celery_result_backend=_getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
            or "redis://localhost:6379/1",
            celery_task_always_eager=_parse_bool(
                _getenv("CELERY_TASK_ALWAYS_EAGER"), default=environment == "local"
            ),
            admin_emails=[
                email.strip().lower()
                for email in (_getenv("ADMIN_EMAILS", "") or "").split(",")
                if email.strip()
            ],
            cors_origins=[
                origin.strip()
                for origin in (_getenv("CORS_ORIGINS", "") or "").split(",")
                if origin.strip()
            ],
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
