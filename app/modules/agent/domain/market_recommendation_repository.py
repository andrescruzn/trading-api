# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/market_recommendation_repository.py
#
# Contrato del repositorio de recomendaciones de mercados de la IA.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.common.contracts import TransactionalRepository
from app.modules.agent.domain.market_recommendation_entity import MarketRecommendation


class MarketRecommendationRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, recommendation: MarketRecommendation) -> MarketRecommendation:
        ...

    @abstractmethod
    def get_latest(self) -> MarketRecommendation | None:
        ...
