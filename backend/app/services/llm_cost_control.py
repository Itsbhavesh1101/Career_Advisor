from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class LLMRequestBudget:
    daily_limit: int
    user_daily_limit: int
    prompt_max_chars: int
    output_token_cap: int
    endpoint_daily_limits: dict[str, int]


class _LLMBudgetState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._current_day = date.today()
        self._request_count = 0
        self._user_request_counts: dict[str, int] = {}
        self._endpoint_request_counts: dict[str, int] = {}
        self._usage_stats: dict[tuple[str, str, str], dict[str, int]] = {}
        self._event_counts: dict[tuple[str, str, str], int] = {}

    def _rollover_if_needed(self) -> None:
        today = date.today()
        if today == self._current_day:
            return
        self._current_day = today
        self._request_count = 0
        self._user_request_counts = {}
        self._endpoint_request_counts = {}
        self._usage_stats = {}
        self._event_counts = {}

    def reserve_request(
        self,
        *,
        daily_limit: int,
        user_daily_limit: int,
        user_key: str,
        endpoint: str,
        endpoint_daily_limit: int,
    ) -> None:
        with self._lock:
            self._rollover_if_needed()

            if self._request_count >= daily_limit:
                raise RuntimeError("LLM daily request budget exceeded.")

            user_count = self._user_request_counts.get(user_key, 0)
            if user_count >= user_daily_limit:
                raise RuntimeError("LLM per-user daily request budget exceeded.")

            endpoint_count = self._endpoint_request_counts.get(endpoint, 0)
            if endpoint_count >= endpoint_daily_limit:
                raise RuntimeError(f"LLM endpoint budget exceeded for '{endpoint}'.")

            self._request_count += 1
            self._user_request_counts[user_key] = user_count + 1
            self._endpoint_request_counts[endpoint] = endpoint_count + 1

    def record_usage(
        self,
        *,
        user_key: str,
        endpoint: str,
        usage_scope: str,
        prompt_chars: int,
        output_chars: int,
        total_tokens: int,
    ) -> dict[str, int]:
        with self._lock:
            self._rollover_if_needed()
            key = (user_key, endpoint, usage_scope)
            existing = self._usage_stats.get(
                key,
                {"requests": 0, "prompt_chars": 0, "output_chars": 0, "tokens": 0},
            )
            existing["requests"] += 1
            existing["prompt_chars"] += max(prompt_chars, 0)
            existing["output_chars"] += max(output_chars, 0)
            existing["tokens"] += max(total_tokens, 0)
            self._usage_stats[key] = existing
            return dict(existing)

    def get_usage(self, user_key: str, endpoint: str, usage_scope: str) -> dict[str, int]:
        with self._lock:
            self._rollover_if_needed()
            key = (user_key, endpoint, usage_scope)
            existing = self._usage_stats.get(
                key,
                {"requests": 0, "prompt_chars": 0, "output_chars": 0, "tokens": 0},
            )
            return dict(existing)

    def record_event(self, *, user_key: str, endpoint: str, event: str) -> int:
        with self._lock:
            self._rollover_if_needed()
            key = (user_key, endpoint, event)
            next_value = self._event_counts.get(key, 0) + 1
            self._event_counts[key] = next_value
            return next_value

    def get_events(self, user_key: str, endpoint: str) -> dict[str, int]:
        with self._lock:
            self._rollover_if_needed()
            results: dict[str, int] = {}
            for (target_user, target_endpoint, event), count in self._event_counts.items():
                if target_user == user_key and target_endpoint == endpoint:
                    results[event] = count
            return results


_BUDGET_STATE = _LLMBudgetState()


def reserve_llm_request(budget: LLMRequestBudget, *, user_key: str, endpoint: str) -> None:
    endpoint_limit = budget.endpoint_daily_limits.get(endpoint, budget.daily_limit)
    _BUDGET_STATE.reserve_request(
        daily_limit=budget.daily_limit,
        user_daily_limit=budget.user_daily_limit,
        user_key=user_key,
        endpoint=endpoint,
        endpoint_daily_limit=endpoint_limit,
    )


def record_llm_usage(
    *,
    user_key: str,
    endpoint: str,
    usage_scope: str = "global",
    prompt_chars: int,
    output_chars: int,
    total_tokens: int,
) -> dict[str, int]:
    return _BUDGET_STATE.record_usage(
        user_key=user_key,
        endpoint=endpoint,
        usage_scope=usage_scope,
        prompt_chars=prompt_chars,
        output_chars=output_chars,
        total_tokens=total_tokens,
    )


def get_llm_usage(user_key: str, endpoint: str, usage_scope: str = "global") -> dict[str, Any]:
    return _BUDGET_STATE.get_usage(user_key, endpoint, usage_scope)


def record_llm_event(*, user_key: str, endpoint: str, event: str) -> int:
    return _BUDGET_STATE.record_event(user_key=user_key, endpoint=endpoint, event=event)


def get_llm_events(user_key: str, endpoint: str) -> dict[str, int]:
    return _BUDGET_STATE.get_events(user_key=user_key, endpoint=endpoint)


def enforce_prompt_limit(prompt: str, max_chars: int) -> str:
    if len(prompt) <= max_chars:
        return prompt
    return prompt[:max_chars]


def enforce_token_limit(requested: int, cap: int) -> int:
    return max(1, min(requested, cap))