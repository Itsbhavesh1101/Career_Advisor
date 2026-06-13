from __future__ import annotations

import importlib
import warnings

from pydantic.warnings import PydanticDeprecatedSince20


SCHEMA_MODULES = [
    "app.schemas.company_fit",
    "app.schemas.internship_readiness",
    "app.schemas.placement_risk",
    "app.schemas.role_gap_analysis",
]


def test_read_schemas_use_pydantic_v2_configdict() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", PydanticDeprecatedSince20)

        for module_name in SCHEMA_MODULES:
            module = importlib.import_module(module_name)
            importlib.reload(module)

    deprecated_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, PydanticDeprecatedSince20)
    ]

    assert deprecated_warnings == []
