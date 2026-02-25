# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.market.domain.timeframe_entity import Timeframe
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class ListTimeframesService:
    """Lista todos los timeframes ordenados por duración."""

    def __init__(self, repo: TimeframeRepository):
        self._repo = repo

    def list(self) -> ServiceResult[list[Timeframe]]:
        timeframes = self._repo.list_all()
        return ServiceResult.ok(data=timeframes)
