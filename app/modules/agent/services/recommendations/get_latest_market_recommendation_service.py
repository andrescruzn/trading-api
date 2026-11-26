# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/services/recommendations/get_latest_market_recommendation_service.py
#
# Última recomendación de mercados de la IA (o None si aún no hay).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.agent.domain.market_recommendation_entity import MarketRecommendation
from app.modules.agent.domain.market_recommendation_repository import (
    MarketRecommendationRepository,
)


class GetLatestMarketRecommendationService:
    """Lee la recomendación más reciente; no llama a la IA."""

    def __init__(self, repo: MarketRecommendationRepository):
        self._repo = repo

    def get(self) -> ServiceResult[MarketRecommendation | None]:
        return ServiceResult.ok(data=self._repo.get_latest())
