from __future__ import annotations

from typing import Any

from app.core.scoring import PSYCHOMETRIC_SCORING

_DEFAULT_TRAITS = {
    "analytical": 0.5,
    "creativity": 0.5,
    "execution": 0.5,
    "collaboration": 0.5,
    "risk_tolerance": 0.5,
    "learning_agility": 0.5,
    "domain_curiosity": 0.5,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class PsychometricTraitService:
    def initial_traits(self) -> dict[str, float]:
        if isinstance(PSYCHOMETRIC_SCORING.traits, dict) and PSYCHOMETRIC_SCORING.traits:
            return {k: float(v) for k, v in PSYCHOMETRIC_SCORING.traits.items()}
        return dict(_DEFAULT_TRAITS)

    def apply_trait_effect(
        self,
        *,
        current_traits: dict[str, float],
        trait_effect: dict[str, float],
        questions_answered: int,
        min_questions: int,
        previous_state: dict[str, Any] | None = None,
    ) -> tuple[dict[str, float], float, dict[str, Any]]:
        traits = dict(current_traits)
        for trait, delta in trait_effect.items():
            traits[trait] = _clamp(float(traits.get(trait, 0.5)) + float(delta))

        magnitude = 0.0
        if trait_effect:
            magnitude = sum(abs(float(v)) for v in trait_effect.values()) / len(trait_effect)

        prior_history = []
        if isinstance(previous_state, dict):
            candidate = previous_state.get("delta_history")
            if isinstance(candidate, list):
                prior_history = [float(v) for v in candidate if isinstance(v, (float, int))]

        history = (prior_history + [magnitude])[-6:]
        average_magnitude = sum(history) / len(history)

        # Stability improves when trait changes become less volatile.
        stability = max(0.0, 1.0 - (average_magnitude / 0.35))

        progress = min(1.0, questions_answered / max(min_questions, 1))
        confidence = _clamp((0.6 * progress) + (0.4 * stability))

        return traits, confidence, {
            "last_trait_effect": trait_effect,
            "delta_magnitude": magnitude,
            "delta_history": history,
        }
