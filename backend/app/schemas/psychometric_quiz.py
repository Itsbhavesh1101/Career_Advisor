from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MAX_RECORDED_RESPONSE_MS = 300000


class StrictQuizSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PsychometricQuestionOption(StrictQuizSchemaModel):
    option_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=140)
    trait_effect: dict[str, float]

    @model_validator(mode="after")
    def _validate_trait_effect(self) -> "PsychometricQuestionOption":
        if not self.trait_effect:
            raise ValueError("trait_effect cannot be empty")
        for trait, delta in self.trait_effect.items():
            if not trait.strip():
                raise ValueError("trait key cannot be empty")
            if delta < -0.35 or delta > 0.35:
                raise ValueError("trait deltas must be within -0.35..0.35")
        return self


class PsychometricQuestionLLMOutput(StrictQuizSchemaModel):
    question: str = Field(min_length=1, max_length=180)
    trait_tag: str = Field(min_length=1, max_length=80)
    options: list[PsychometricQuestionOption] = Field(min_length=3, max_length=4)


class PsychometricQuestionRead(StrictQuizSchemaModel):
    id: str
    session_id: str
    position: int
    source: str
    trait_tag: str | None = None
    question_text: str
    options: list[PsychometricQuestionOption]
    schema_version: str
    prompt_version: str


class PsychometricSessionStatusRead(StrictQuizSchemaModel):
    session_id: str
    status: str
    fallback_mode: bool
    breaker_open: bool
    ai_status: str = "calibrating"
    adaptation_reason: str | None = None
    next_focus: str | None = None
    questions_answered: int
    min_questions: int
    max_questions: int
    confidence: float
    current_traits: dict[str, float]
    current_state: dict
    current_question: PsychometricQuestionRead | None = None
    created_at: datetime
    updated_at: datetime


class PsychometricSessionStartRead(StrictQuizSchemaModel):
    session: PsychometricSessionStatusRead


class PsychometricAnswerSubmit(StrictQuizSchemaModel):
    question_id: str
    option_id: str
    answer_id: str = Field(default_factory=lambda: str(uuid4()))
    idempotency_key: str | None = Field(default=None, max_length=80)
    response_ms: int | None = Field(default=None, ge=0, le=86400000)

    @field_validator("response_ms")
    @classmethod
    def _cap_stale_response_ms(cls, value: int | None) -> int | None:
        if value is None:
            return None
        return min(value, MAX_RECORDED_RESPONSE_MS)


class PsychometricAnswerRead(StrictQuizSchemaModel):
    answer_id: str
    accepted: bool
    duplicate: bool = False
    session: PsychometricSessionStatusRead


class PsychometricAbandonSubmit(StrictQuizSchemaModel):
    reason: str | None = Field(default=None, max_length=80)


class PsychometricResultRead(StrictQuizSchemaModel):
    session_id: str
    student_profile_id: int
    user_id: int
    trait_scores: dict[str, float]
    confidence: float
    question_count: int
    fallback_count: int
    trait_version: str
    schema_version: str
    prompt_version: str
    scoring_config_hash: str
    completed_at: datetime
