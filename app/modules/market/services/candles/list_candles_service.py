# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class ListCandlesService:
    """Retorna velas OHLCV para un símbolo y timeframe con filtros de fecha."""

    def __init__(
        self,
        candle_repo: CandleRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
    ):
        self._candle_repo = candle_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo

    def list(
        self,
        symbol_id: int,
        timeframe_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> ServiceResult[list[Candle]]:
        # Validar que el símbolo existe
        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        # Validar que el timeframe existe
        tf = self._timeframe_repo.get_by_id(timeframe_id)
        if tf is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)

        # Limitar a máximo 1000 velas por petición
        safe_limit = min(max(1, limit), 1000)

        candles = self._candle_repo.list_candles(
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=safe_limit,
        )
        return ServiceResult.ok(data=candles)
