# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository


class GetStrategyService:
    """Obtiene una estrategia por su ID."""

    def __init__(self, repo: StrategyRepository):
        self._repo = repo

    def get(self, strategy_id: int) -> ServiceResult[Strategy]:
        strategy = self._repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(code="STRATEGY_NOT_FOUND", http_status=404)
        return ServiceResult.ok(data=strategy)
