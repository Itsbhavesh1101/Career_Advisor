from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings, get_settings


DEFAULT_HASH_MODEL = "local-token-hash-v1"
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.]+")


@dataclass(frozen=True)
class EmbeddingResult:
    values: list[float]
    provider: str
    model: str

    @property
    def dimensions(self) -> int:
        return len(self.values)


class EmbeddingProvider(Protocol):
    provider: str
    model: str
    dimensions: int

    def embed(self, text: str) -> EmbeddingResult:
        ...


class HashEmbeddingProvider:
    provider = "hash"
    model = DEFAULT_HASH_MODEL

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 8:
            raise ValueError("Embedding dimensions must be >= 8.")
        self.dimensions = dimensions

    def embed(self, text: str) -> EmbeddingResult:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in sorted(_tokens(text)):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (len(token) / 24.0)
            vector[bucket] += sign * weight

        return EmbeddingResult(
            values=_normalize(vector),
            provider=self.provider,
            model=self.model,
        )


class BedrockTitanEmbeddingProvider:
    provider = "bedrock"

    def __init__(
        self,
        *,
        region_name: str,
        model: str,
        dimensions: int,
        timeout_seconds: int,
    ) -> None:
        import boto3
        from botocore.config import Config

        self.model = model
        self.dimensions = dimensions
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
            config=Config(read_timeout=timeout_seconds, connect_timeout=timeout_seconds),
        )

    def embed(self, text: str) -> EmbeddingResult:
        body = json.dumps(
            {
                "inputText": text[:50000],
                "dimensions": self.dimensions,
                "normalize": True,
            }
        )
        response = self._client.invoke_model(
            body=body,
            modelId=self.model,
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        values = payload.get("embedding")
        if not isinstance(values, list) or len(values) != self.dimensions:
            raise RuntimeError("Bedrock embedding response did not match configured dimensions.")
        return EmbeddingResult(
            values=[float(value) for value in values],
            provider=self.provider,
            model=self.model,
        )


def create_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.rag_embedding_provider == "bedrock":
        region = settings.rag_embedding_bedrock_region or settings.bedrock_region
        if not region:
            raise RuntimeError(
                "RAG_EMBEDDING_BEDROCK_REGION or BEDROCK_REGION is required for Bedrock embeddings."
            )
        return BedrockTitanEmbeddingProvider(
            region_name=region,
            model=settings.rag_embedding_model,
            dimensions=settings.rag_embedding_dimensions,
            timeout_seconds=settings.rag_embedding_timeout_seconds,
        )
    return HashEmbeddingProvider(dimensions=settings.rag_embedding_dimensions)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        _magnitude(left) * _magnitude(right) or 1.0
    )


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def parse_vector_literal(value: str | None) -> list[float] | None:
    if not value:
        return None
    text = value.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return None
    try:
        return [float(item) for item in text[1:-1].split(",") if item.strip()]
    except ValueError:
        return None


def _normalize(values: list[float]) -> list[float]:
    magnitude = _magnitude(values)
    if magnitude <= 0:
        return values
    return [value / magnitude for value in values]


def _magnitude(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(value)}
