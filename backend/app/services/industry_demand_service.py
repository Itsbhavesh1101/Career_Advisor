from __future__ import annotations

from app.schemas.industry_demand import IndustryDemandRead, IndustryTrend
from app.services.llm_client import LLMClient


class IndustryDemandService:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def get_trends(self, year: int = 2026, user_id: int | None = None) -> IndustryDemandRead:
        trends = self._llm_trends(year, user_id=user_id)
        return IndustryDemandRead(year=year, trends=trends)

    def _llm_trends(self, year: int, user_id: int | None = None) -> list[IndustryTrend]:
        system_prompt = (
            "You are a labor market analyst. Provide top industry skills trends "
            "for the given year. Return ONLY valid JSON."
        )
        user_prompt = (
            f"Return the top 5-7 skills in demand for {year}.\n"
            "Required JSON format:\n"
            "{\n"
            '  "trends":[{"trend":"AI Agents","impact":"high"}]\n'
            "}\n"
            "impact must be: high | medium | low."
        )
        data = self.llm.generate_industry_trends(
            system_prompt,
            user_prompt,
            user_id=user_id,
        )
        trends = data.get("trends", [])
        return [IndustryTrend(**item) for item in trends if "trend" in item]
