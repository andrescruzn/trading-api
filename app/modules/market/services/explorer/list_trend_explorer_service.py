# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/services/explorer/list_trend_explorer_service.py
#
# Ranking de mercados por fuerza de tendencia (explorador de M2), con las
# estadísticas de 24 h de cada mercado (precio, variación, volumen).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.ccxt_exchanges import is_perpetual, supports_auto_fetch
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.ticker_gateway import Ticker, TickerGateway
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.market.services.explorer.trend_metrics import TrendMetrics, compute_trend_metrics

EXPLORER_TIMEFRAME = "1d"
# 200 para la EMA200 + margen para el rendimiento de 90 días
EXPLORER_CANDLES = 250


@dataclass(frozen=True)
class TrendRow:
    symbol: Symbol
    is_perpetual: bool
    metrics: TrendMetrics | None  # None = sin velas diarias suficientes
    ticker: Ticker | None = None  # None = sin datos en vivo (exchange caído)


class ListTrendExplorerService:
    """
    Ordena los símbolos activos por fuerza de tendencia con sus velas 1d.

    Reglas:
    - Solo símbolos cuyas velas se descargan solas (`supports_auto_fetch`):
      los demás no podrían tener un agente.
    - Orden: `score` descendente (alcistas fuertes primero, bajistas al
      final, porque la app no abre cortos) y, a igual score, `strength`.
      Los que no tienen datos van al final.
    - Las velas salen de la BD (las trae RefreshExplorerCandlesService).
    - Los datos de 24 h salen del exchange vía `ticker_gateway` (opcional).
      Si falla, el ranking se devuelve igual, con `ticker=None`.
    """

    def __init__(
        self,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        candle_repo: CandleRepository,
        ticker_gateway: TickerGateway | None = None,
    ):
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._candle_repo = candle_repo
        self._ticker_gateway = ticker_gateway

    def list(self, asset_class: str | None = None) -> ServiceResult[list[TrendRow]]:
        timeframe = self._timeframe_repo.get_by_code(EXPLORER_TIMEFRAME)
        if timeframe is None:
            return ServiceResult.fail(code="EXPLORER_TIMEFRAME_MISSING", http_status=404)

        symbols = [
            s
            for s in self._symbol_repo.list_all(asset_class=asset_class, is_active=True)
            if supports_auto_fetch(s.exchange_name)
        ]
        tickers = self._fetch_tickers(symbols)

        rows: list[TrendRow] = []
        for symbol in symbols:
            candles = self._candle_repo.list_candles(
                symbol_id=symbol.id, timeframe_id=timeframe.id, limit=EXPLORER_CANDLES
            )
            rows.append(
                TrendRow(
                    symbol=symbol,
                    is_perpetual=is_perpetual(symbol.symbol),
                    metrics=compute_trend_metrics(candles),
                    ticker=tickers.get(symbol.symbol),
                )
            )

        rows.sort(key=_sort_key, reverse=True)
        return ServiceResult.ok(data=rows)

    def _fetch_tickers(self, symbols: list[Symbol]) -> dict[str, Ticker]:
        if self._ticker_gateway is None or not symbols:
            return {}
        return self._ticker_gateway.fetch([s.symbol for s in symbols])


def _sort_key(row: TrendRow) -> tuple[int, float, float]:
    if row.metrics is None:
        return (0, 0.0, 0.0)
    return (1, row.metrics.score, row.metrics.strength)
