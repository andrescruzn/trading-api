# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository


class ListStrategiesService:
    """Lista todas las estrategias disponibles."""

    def __init__(self, repo: StrategyRepository):
        self._repo = repo

    def list(self) -> ServiceResult[list[Strategy]]:
        strategies = self._repo.list_all()
        return ServiceResult.ok(data=strategies)
