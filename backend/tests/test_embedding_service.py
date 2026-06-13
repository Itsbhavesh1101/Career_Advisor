from __future__ import annotations

import math

from app.services.embedding_service import (
    HashEmbeddingProvider,
    cosine_similarity,
    vector_literal,
)


def test_hash_embedding_provider_returns_stable_normalized_dimensions() -> None:
    provider = HashEmbeddingProvider(dimensions=256)

    first = provider.embed("AIML students need Python projects and ML labs")
    second = provider.embed("AIML students need Python projects and ML labs")

    assert first.values == second.values
    assert first.dimensions == 256
    assert first.provider == "hash"
    assert first.model == "local-token-hash-v1"
    norm = math.sqrt(sum(value * value for value in first.values))
    assert norm == pytest_approx(1.0)


def test_hash_embeddings_rank_related_text_above_unrelated_text() -> None:
    provider = HashEmbeddingProvider(dimensions=256)
    query = provider.embed("Python machine learning placement readiness")
    related = provider.embed("AIML placement needs Python ML projects")
    unrelated = provider.embed("Scholarship transport hostel fee policy")

    assert cosine_similarity(query.values, related.values) > cosine_similarity(
        query.values,
        unrelated.values,
    )


def test_vector_literal_formats_pgvector_input() -> None:
    literal = vector_literal([0.125, -0.5, 1.0])

    assert literal == "[0.125000,-0.500000,1.000000]"


def pytest_approx(value: float):
    import pytest

    return pytest.approx(value, rel=1e-6, abs=1e-6)
