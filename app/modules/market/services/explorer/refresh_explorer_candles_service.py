# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/services/explorer/refresh_explorer_candles_service.py
#
# Descarga las velas diarias que necesita el explorador de tendencia.
# ======================================================================

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.ccxt_exchanges import supports_auto_fetch
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.market.services.candles.fetch_candles_service import FetchCandlesService
from app.modules.market.services.explorer.list_trend_explorer_service import (
    EXPLORER_CANDLES,
    EXPLORER_TIMEFRAME,
)

_DAY_SECONDS = 86400


class RefreshExplorerCandlesService:
    """
    Trae velas 1d de todos los símbolos activos con descarga automática.

    Reglas:
    - Sin `force`, solo descarga los símbolos cuya última vela diaria
      tiene un día o más (lo que usa el scheduler una vez al día).
    - Con `force` descarga todos: refresca también la vela del día en
      curso (botón "Actualizar datos" del admin).
    - Si no hay velas, carga EXPLORER_CANDLES; si las hay, solo los días
      que faltan más un margen.
    - Un símbolo que falla no detiene a los demás: se informa en `failed`.
    - Un cliente ccxt por exchange para todo el lote (cada cliente nuevo
      vuelve a cargar los mercados del exchange).
    """

    def __init__(
        self,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        candle_repo: CandleRepository,
        fetch_service: FetchCandlesService,
    ):
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._candle_repo = candle_repo
        self._fetch_service = fetch_service

    def refresh(self, force: bool = False) -> ServiceResult[dict[str, Any]]:
        timeframe = self._timeframe_repo.get_by_code(EXPLORER_TIMEFRAME)
        if timeframe is None:
            return ServiceResult.fail(code="EXPLORER_TIMEFRAME_MISSING", http_status=404)

        now = utc_now()
        client_cache: dict[str, Any] = {}
        updated: list[str] = []
        skipped: list[str] = []
        failed: list[dict[str, str]] = []

        for symbol in self._symbol_repo.list_all(is_active=True):
            if not supports_auto_fetch(symbol.exchange_name):
                continue

            latest = self._candle_repo.get_latest_ts(symbol.id, timeframe.id)
            if latest is None:
                limit = EXPLORER_CANDLES
            else:
                days_behind = int((now - latest).total_seconds() // _DAY_SECONDS)
                if days_behind < 1 and not force:
                    skipped.append(symbol.symbol)
                    continue
                limit = min(EXPLORER_CANDLES, days_behind + 2)

            result = self._fetch_service.fetch(
                symbol_id=symbol.id,
                timeframe_id=timeframe.id,
                limit=limit,
                client_cache=client_cache,
            )
            if result.success:
                updated.append(symbol.symbol)
            else:
                code = result.error.code if result.error else "UNKNOWN"
                failed.append({"symbol": symbol.symbol, "code": code})

        return ServiceResult.ok(data={"updated": updated, "skipped": skipped, "failed": failed})
