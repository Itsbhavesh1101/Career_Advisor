from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.institution import InstitutionCatalog, InstitutionOverridePayload
from app.services.institution_config_service import InstitutionConfigService


class _FakeDB:
    def __init__(self, rows: list[object] | None = None, saved: object | None = None) -> None:
        self.rows = rows or []
        self.saved = saved
        self.added = None
        self.committed = False
        self.refreshed = None

    def scalars(self, _stmt):
        rows = self.rows

        class _Result:
            def all(self) -> list[object]:
                return rows

        return _Result()

    def scalar(self, _stmt):
        return self.saved

    def add(self, row) -> None:
        self.added = row
        self.saved = row

    def commit(self) -> None:
        self.committed = True

    def refresh(self, row) -> None:
        self.refreshed = row


def test_catalog_loads_seeded_sage_programs() -> None:
    service = InstitutionConfigService()

    catalog = service.get_catalog()

    assert catalog.version == "sage-initial-2026-05"
    assert catalog.institution_name == "SAGE Group of Institutions"
    assert len(catalog.schools) >= 3
    assert any(
        program.program_id == "sirt-btech-cse-aiml"
        for school in catalog.schools
        for program in school.programs
    )


def test_catalog_loads_generic_programs_when_mode_is_generic(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.institution_config_service.get_settings",
        lambda: SimpleNamespace(institution_mode="generic"),
    )

    catalog = InstitutionConfigService().get_catalog()
    catalog_json = catalog.model_dump_json()

    assert catalog.version == "generic-initial-2026-05"
    assert catalog.institution_name == "Partner Institution"
    assert any(
        program.program_id == "generic-btech-cse-ai"
        for school in catalog.schools
        for program in school.programs
    )
    assert "SAGE" not in catalog_json
    assert "SIRT" not in catalog_json


def test_branding_defaults_to_sage_mode() -> None:
    branding = InstitutionConfigService().get_branding()

    assert branding.mode == "sage"
    assert branding.product_name == "SAGE Career Navigator"
    assert branding.institution_short_name == "SAGE/SIRT"


def test_branding_uses_generic_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.institution_config_service.get_settings",
        lambda: SimpleNamespace(institution_mode="generic"),
    )

    branding = InstitutionConfigService().get_branding()
    branding_json = branding.model_dump_json()

    assert branding.mode == "generic"
    assert branding.product_name == "Student Success Navigator"
    assert branding.institution_name == "Partner Institution"
    assert "SAGE" not in branding_json
    assert "SIRT" not in branding_json


def test_find_program_returns_school_and_program() -> None:
    service = InstitutionConfigService()

    match = service.find_program("sirt-btech-cse-cyber")

    assert match is not None
    school, program = match
    assert school.school_id == "sirt-engineering"
    assert program.program_name == "B.Tech CSE - Cyber Security"


def test_catalog_filters_inactive_programs() -> None:
    service = InstitutionConfigService()

    catalog = service.get_catalog()
    inactive_program_ids = {
        program.program_id
        for school in catalog.schools
        for program in school.programs
        if not program.is_active
    }
    inactive_school_program_ids = {
        program.program_id
        for school in catalog.schools
        if not school.is_active
        for program in school.programs
    }

    assert "sirt-btech-civil-legacy" in inactive_program_ids
    assert "sage-legacy-bca" in inactive_school_program_ids

    active_programs = service.list_active_programs()
    active_program_ids = {program.program_id for program in active_programs}

    assert active_programs
    assert all(program.is_active for program in active_programs)
    assert inactive_program_ids.isdisjoint(active_program_ids)
    assert inactive_school_program_ids.isdisjoint(active_program_ids)


def test_get_catalog_returns_isolated_copy() -> None:
    service = InstitutionConfigService()

    first_catalog = service.get_catalog()
    first_catalog.schools[0].programs[0].program_name = "Mutated Program Name"

    second_catalog = service.get_catalog()

    assert second_catalog.schools[0].programs[0].program_name == "B.Tech CSE - AIML"


def test_find_program_is_active_only_by_default() -> None:
    service = InstitutionConfigService()

    assert service.find_program("sirt-btech-civil-legacy") is None
    assert service.find_program("sage-legacy-bca") is None

    inactive_program_match = service.find_program("sirt-btech-civil-legacy", active_only=False)
    inactive_school_match = service.find_program("sage-legacy-bca", active_only=False)

    assert inactive_program_match is not None
    assert inactive_school_match is not None


def test_catalog_validation_rejects_duplicate_school_ids() -> None:
    catalog = InstitutionConfigService().get_catalog().model_dump()
    catalog["schools"][1]["school_id"] = catalog["schools"][0]["school_id"]

    with pytest.raises(ValidationError, match="Duplicate school_id"):
        InstitutionCatalog.model_validate(catalog)


def test_catalog_validation_rejects_duplicate_branch_ids_within_program() -> None:
    catalog = InstitutionConfigService().get_catalog().model_dump()
    catalog["schools"][0]["programs"][0]["branches"] = [
        {"branch_id": "bhopal-main", "branch_name": "Bhopal Main"},
        {"branch_id": "bhopal-main", "branch_name": "Bhopal East"},
    ]

    with pytest.raises(ValidationError, match="Duplicate branch_id"):
        InstitutionCatalog.model_validate(catalog)


def test_admin_overrides_merge_priority_skills() -> None:
    row = SimpleNamespace(
        key="default",
        value={
            "placement_ready_threshold": 80,
            "admission_high_intent_threshold": 72,
            "priority_skills_by_program": {
                "sirt-btech-cse-aiml": ["Python", "Prompt Engineering"]
            },
            "counselor_notes_by_program": {
                "sirt-btech-cse-aiml": ["Check mathematics readiness before admission close."]
            },
        },
    )
    service = InstitutionConfigService(_FakeDB(saved=row))

    merged = service.get_effective_overrides()

    assert merged.placement_ready_threshold == 80
    assert merged.admission_high_intent_threshold == 72
    assert merged.priority_skills_by_program["sirt-btech-cse-aiml"] == [
        "Python",
        "Prompt Engineering",
    ]


def test_effective_overrides_uses_only_default_row() -> None:
    non_default_row = SimpleNamespace(
        key="experimental",
        value={
            "placement_ready_threshold": 99,
            "priority_skills_by_program": {"sage-bba": ["Ignored"]},
        },
    )
    default_row = SimpleNamespace(
        key="default",
        value={
            "placement_ready_threshold": 81,
            "priority_skills_by_program": {"sage-bba": ["Communication"]},
        },
    )
    service = InstitutionConfigService(_FakeDB([non_default_row], saved=default_row))

    merged = service.get_effective_overrides()

    assert merged.placement_ready_threshold == 81
    assert merged.priority_skills_by_program == {"sage-bba": ["Communication"]}


def test_upsert_default_overrides_creates_default_row() -> None:
    db = _FakeDB()
    payload = InstitutionOverridePayload(
        placement_ready_threshold=82,
        priority_skills_by_program={"sage-bba": ["Communication"]},
    )

    row = InstitutionConfigService(db).upsert_default_overrides(payload)

    assert row.key == "default"
    assert row.value["placement_ready_threshold"] == 82
    assert row.value["priority_skills_by_program"] == {"sage-bba": ["Communication"]}
    assert db.added is row
    assert db.committed is True
    assert db.refreshed is row


def test_upsert_default_overrides_replaces_existing_default_row() -> None:
    existing = SimpleNamespace(
        key="default",
        value={
            "placement_ready_threshold": 75,
            "priority_skills_by_program": {"sage-bba": ["Old"]},
        },
    )
    db = _FakeDB(saved=existing)
    payload = InstitutionOverridePayload(
        placement_ready_threshold=88,
        admission_high_intent_threshold=74,
        priority_skills_by_program={"sage-bba": ["Communication", "Excel"]},
    )

    row = InstitutionConfigService(db).upsert_default_overrides(payload)

    assert row is existing
    assert row.value == payload.model_dump()
    assert db.added is None
    assert db.committed is True
    assert db.refreshed is row
