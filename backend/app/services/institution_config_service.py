from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.admin_management import AdminManagedItem
from app.models.institution_override import InstitutionOverride
from app.schemas.institution import (
    InstitutionBranding,
    InstitutionCatalog,
    InstitutionOverridePayload,
    InstitutionProgram,
    InstitutionSchool,
)


CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
CATALOG_PATHS = {
    "sage": CONFIG_DIR / "institution_programs.json",
    "generic": CONFIG_DIR / "institution_programs_generic.json",
}

BRANDING_BY_MODE = {
    "sage": InstitutionBranding(
        mode="sage",
        product_name="SAGE Career Navigator",
        institution_name="SAGE Group of Institutions",
        institution_short_name="SAGE/SIRT",
        homepage={
            "headline": "SAGE Career Navigator",
            "description": (
                "Choose the right academic path, build placement readiness, and keep every "
                "recommendation connected to the student's goals, strengths, and next action."
            ),
            "feature_intro": (
                "SAGE combines student intake, AI analysis, personalized copilot support, "
                "and practical readiness tools in the same workflow."
            ),
        },
        auth={
            "signup_title": "Create your SAGE workspace",
            "login_title": "Continue your SAGE journey",
            "profile_empty": (
                "Create your SAGE profile so the dashboard can recommend the right next step."
            ),
        },
        branch_guidance={
            "title": "Find my best-fit SAGE/SIRT program",
            "description": (
                "For 12th students choosing a branch with subject strengths, interests, "
                "confidence, and expectations."
            ),
            "workflow": (
                "Turn subjects, interests, confidence, and expectations into SAGE/SIRT "
                "program guidance."
            ),
        },
        placement_readiness={
            "title": "Build my placement readiness plan",
            "description": (
                "For college students connecting skills, projects, resume, training, "
                "internships, and career goals."
            ),
        },
        admin_command={
            "title": "Open the command center",
            "description": (
                "For administrators reviewing readiness, student risk, knowledge quality, "
                "and priority actions."
            ),
        },
    ),
    "generic": InstitutionBranding(
        mode="generic",
        product_name="Student Success Navigator",
        institution_name="Partner Institution",
        institution_short_name="Partner Institution",
        homepage={
            "headline": "Student Success Navigator",
            "description": (
                "Choose the right academic path, build placement readiness, and keep every "
                "recommendation connected to the student's goals, strengths, and next action."
            ),
            "feature_intro": (
                "The platform combines student intake, AI analysis, personalized copilot "
                "support, and practical readiness tools in the same workflow."
            ),
        },
        auth={
            "signup_title": "Create your student success workspace",
            "login_title": "Continue your student success journey",
            "profile_empty": (
                "Create your profile so the dashboard can recommend the right next step."
            ),
        },
        branch_guidance={
            "title": "Find my best-fit program",
            "description": (
                "For school students choosing a branch with subject strengths, interests, "
                "confidence, and expectations."
            ),
            "workflow": (
                "Turn subjects, interests, confidence, and expectations into program guidance."
            ),
        },
        placement_readiness={
            "title": "Build my placement readiness plan",
            "description": (
                "For college students connecting skills, projects, resume, training, "
                "internships, and career goals."
            ),
        },
        admin_command={
            "title": "Open the command center",
            "description": (
                "For administrators reviewing readiness, student risk, knowledge quality, "
                "and priority actions."
            ),
        },
    ),
}


@lru_cache(maxsize=2)
def _load_catalog(mode: str) -> InstitutionCatalog:
    catalog_path = CATALOG_PATHS.get(mode, CATALOG_PATHS["sage"])
    with catalog_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return InstitutionCatalog.model_validate(data)


class InstitutionConfigService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def _mode(self) -> str:
        return get_settings().institution_mode

    def get_branding(self) -> InstitutionBranding:
        return BRANDING_BY_MODE[self._mode()].model_copy(deep=True)

    def get_catalog(self) -> InstitutionCatalog:
        catalog = _load_catalog(self._mode()).model_copy(deep=True)
        if self.db is None or not hasattr(self.db, "scalars"):
            return catalog
        return self._with_managed_programs(catalog)

    def list_active_programs(self) -> list[InstitutionProgram]:
        programs: list[InstitutionProgram] = []
        for school in self.get_catalog().schools:
            if not school.is_active:
                continue
            programs.extend(program for program in school.programs if program.is_active)
        return programs

    def find_program(
        self, program_id: str, *, active_only: bool = True
    ) -> tuple[InstitutionSchool, InstitutionProgram] | None:
        for school in self.get_catalog().schools:
            if active_only and not school.is_active:
                continue
            for program in school.programs:
                if active_only and not program.is_active:
                    continue
                if program.program_id == program_id:
                    return school, program
        return None

    def get_effective_overrides(self) -> InstitutionOverridePayload:
        merged = InstitutionOverridePayload()
        if self.db is None:
            return merged

        row = self.db.scalar(
            select(InstitutionOverride).where(InstitutionOverride.key == "default")
        )
        if row is None:
            return merged

        payload = merged.model_dump()
        payload.update(row.value)
        return InstitutionOverridePayload.model_validate(payload)

    def upsert_default_overrides(
        self, payload: InstitutionOverridePayload
    ) -> InstitutionOverride:
        if self.db is None:
            raise ValueError("Database session is required for override updates")

        row = self.db.scalar(
            select(InstitutionOverride).where(InstitutionOverride.key == "default")
        )
        if row is None:
            row = InstitutionOverride(key="default", value=payload.model_dump())
            self.db.add(row)
        else:
            row.value = payload.model_dump()

        self.db.commit()
        self.db.refresh(row)
        return row

    def _with_managed_programs(
        self, catalog: InstitutionCatalog
    ) -> InstitutionCatalog:
        rows = self.db.scalars(
            select(AdminManagedItem)
            .where(AdminManagedItem.item_type == "program")
            .where(AdminManagedItem.status == "active")
            .order_by(AdminManagedItem.title)
        ).all()
        if not rows:
            return catalog

        schools_by_id = {school.school_id: school for school in catalog.schools}
        for row in rows:
            program = self._program_from_managed_item(row)
            if program is None:
                continue
            payload = row.payload or {}
            school_id = str(payload.get("school_id") or "admin-managed")
            school = schools_by_id.get(school_id)
            if school is None:
                school = InstitutionSchool(
                    school_id=school_id,
                    school_name=str(
                        payload.get("school_name") or "Admin Managed Programs"
                    ),
                    campus=str(
                        payload.get("campus")
                        or self.get_branding().institution_short_name
                    ),
                    programs=[program],
                )
                schools_by_id[school_id] = school
                catalog.schools.append(school)
                continue

            school.programs = [
                existing
                for existing in school.programs
                if existing.program_id != program.program_id
            ]
            school.programs.append(program)

        return catalog

    def _program_from_managed_item(
        self, row: AdminManagedItem
    ) -> InstitutionProgram | None:
        payload = row.payload or {}
        try:
            return InstitutionProgram(
                program_id=row.slug,
                program_name=row.title,
                degree_level=str(payload.get("degree_level") or "undergraduate"),
                duration_years=float(payload.get("duration_years") or 4),
                is_active=True,
                branches=payload.get("branches") or [],
                priority_skills=_string_list(payload.get("priority_skills")),
                career_paths=_string_list(payload.get("career_paths")),
                admission_fit_signals=_string_list(
                    payload.get("admission_fit_signals")
                ),
                reality_checks=_string_list(payload.get("reality_checks")),
            )
        except ValueError:
            return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
