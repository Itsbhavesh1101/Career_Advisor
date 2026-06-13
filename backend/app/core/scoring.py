from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResumeScoringConfig:
    base_score: int = 50
    skill_points_per_item: int = 2
    skill_points_cap: int = 20
    project_points_per_item: int = 5
    project_points_cap: int = 15
    experience_points_per_item: int = 5
    experience_points_cap: int = 10
    education_points: int = 5
    certification_points: int = 5


@dataclass(frozen=True)
class EmployabilityScoringConfig:
    academic_twelfth_weight: float = 0.5
    academic_cgpa_weight: float = 5.0
    technical_skill_weight: int = 8
    technical_certification_weight: int = 10
    industry_project_weight: int = 12
    industry_internship_weight: int = 20
    resume_project_weight: int = 8
    resume_internship_weight: int = 15
    resume_certification_weight: int = 8
    overall_academic_weight: float = 0.30
    overall_technical_weight: float = 0.30
    overall_industry_weight: float = 0.25
    overall_resume_weight: float = 0.15
    llm_delta_limit: int = 10


@dataclass(frozen=True)
class PlacementRiskScoringConfig:
    cgpa_very_low_threshold: float = 6.5
    cgpa_low_threshold: float = 7.0
    cgpa_very_low_points: int = 3
    cgpa_low_points: int = 2
    low_skill_threshold: int = 4
    low_skill_points: int = 2
    low_project_threshold: int = 2
    low_project_points: int = 2
    no_internship_threshold: int = 1
    no_internship_points: int = 2
    no_certification_threshold: int = 1
    no_certification_points: int = 1
    twelfth_low_threshold: float = 70.0
    twelfth_low_points: int = 1
    high_risk_threshold: int = 7
    medium_risk_threshold: int = 4


@dataclass(frozen=True)
class InternshipReadinessScoringConfig:
    base_score: int = 40
    cgpa_weight: int = 6
    cgpa_cap: int = 25
    project_weight: int = 6
    project_cap: int = 18
    internship_weight: int = 12
    internship_cap: int = 20
    certification_weight: int = 5
    certification_cap: int = 10
    skills_weight: int = 2
    skills_cap: int = 12
    high_readiness_threshold: int = 75
    medium_readiness_threshold: int = 55


@dataclass(frozen=True)
class CompanyFitScoringConfig:
    base_score: int = 50
    project_points_per_item: int = 2
    project_points_cap: int = 8
    internship_points_per_item: int = 4
    internship_points_cap: int = 12
    certification_points_per_item: int = 2
    certification_points_cap: int = 6
    domain_match_points: int = 6
    domain_points_cap: int = 20
    skill_overlap_points_per_skill: int = 2
    skill_overlap_points_cap: int = 10
    cgpa_product_ge_85: int = 10
    cgpa_non_product_ge_85: int = 8
    cgpa_product_ge_80: int = 8
    cgpa_non_product_ge_80: int = 7
    cgpa_product_ge_70: int = 5
    cgpa_non_product_ge_70: int = 6
    cgpa_ge_60: int = 2
    cgpa_product_below_60: int = -2
    cgpa_non_product_below_60: int = 0
    llm_delta_limit: int = 10
    max_results: int = 6


@dataclass(frozen=True)
class PsychometricScoringConfig:
    trait_version: str = "v1"
    min_questions: int = 8
    max_questions: int = 15
    confidence_threshold: float = 0.75
    max_tokens_per_session: int = 3000
    traits: dict[str, float] | None = None


@dataclass(frozen=True)
class ScoringBundle:
    resume: ResumeScoringConfig
    employability: EmployabilityScoringConfig
    placement_risk: PlacementRiskScoringConfig
    internship_readiness: InternshipReadinessScoringConfig
    company_fit: CompanyFitScoringConfig
    psychometric: PsychometricScoringConfig


_DEFAULT_BUNDLE = ScoringBundle(
    resume=ResumeScoringConfig(),
    employability=EmployabilityScoringConfig(),
    placement_risk=PlacementRiskScoringConfig(),
    internship_readiness=InternshipReadinessScoringConfig(),
    company_fit=CompanyFitScoringConfig(),
    psychometric=PsychometricScoringConfig(),
)


def _configs_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "scoring.json"


def _coerce_section(default: Any, candidate: dict[str, Any]) -> Any:
    merged = asdict(default)
    for key in merged:
        if key in candidate:
            merged[key] = candidate[key]
    return type(default)(**merged)


@lru_cache(maxsize=1)
def load_scoring_bundle() -> ScoringBundle:
    path = _configs_path()
    if not path.exists():
        logger.warning("scoring_config_missing path=%s using defaults", path)
        return _DEFAULT_BUNDLE

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("scoring_config_parse_failed path=%s error=%s", path, exc)
        return _DEFAULT_BUNDLE

    try:
        return ScoringBundle(
            resume=_coerce_section(_DEFAULT_BUNDLE.resume, payload.get("resume", {})),
            employability=_coerce_section(
                _DEFAULT_BUNDLE.employability,
                payload.get("employability", {}),
            ),
            placement_risk=_coerce_section(
                _DEFAULT_BUNDLE.placement_risk,
                payload.get("placement_risk", {}),
            ),
            internship_readiness=_coerce_section(
                _DEFAULT_BUNDLE.internship_readiness,
                payload.get("internship_readiness", {}),
            ),
            company_fit=_coerce_section(
                _DEFAULT_BUNDLE.company_fit,
                payload.get("company_fit", {}),
            ),
            psychometric=_coerce_section(
                _DEFAULT_BUNDLE.psychometric,
                payload.get("psychometric", {}),
            ),
        )
    except Exception as exc:
        logger.warning("scoring_config_invalid path=%s error=%s", path, exc)
        return _DEFAULT_BUNDLE


_bundle = load_scoring_bundle()

RESUME_SCORING = _bundle.resume
EMPLOYABILITY_SCORING = _bundle.employability
PLACEMENT_RISK_SCORING = _bundle.placement_risk
INTERNSHIP_READINESS_SCORING = _bundle.internship_readiness
COMPANY_FIT_SCORING = _bundle.company_fit
PSYCHOMETRIC_SCORING = _bundle.psychometric
