# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/services/candles/fetch_candle_history_service.py
#
# PROPÓSITO:
# - Traer del exchange (ccxt, datos públicos, sin claves) las últimas N
#   velas de un símbolo y timeframe, por páginas, SIN guardarlas.
# - Lo usa el backtesting: necesita más historia de la que el scheduler
#   conserva (SCHEDULER_RETENTION_CANDLES, 500 por defecto), y no debe
#   llenar la tabla `candles` con datos que nadie más usa.
# ======================================================================

from __future__ import annotations

from typing import Any

import ccxt

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.market.domain.candle_entity import Candle, candle_from_ccxt_row
from app.modules.market.domain.ccxt_exchanges import ccxt_id_for
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository

# Velas por página (Binance y la mayoría aceptan 1000)
_PAGE_SIZE = 1000
# Tope de páginas por si el exchange devuelve menos de lo pedido
_MAX_PAGES = 20


class FetchCandleHistoryService:
    """Últimas N velas de un par, de la más antigua a la más nueva, en memoria."""

    def __init__(
        self,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        exchange_repo: ExchangeRepository,
        client_factory: Any = None,
    ):
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._exchange_repo = exchange_repo
        # Inyectable en tests: (ccxt_id) -> cliente ccxt
        self._client_factory = client_factory or (
            lambda ccxt_id: getattr(ccxt, ccxt_id)({"enableRateLimit": True})
        )

    def fetch(self, symbol_id: int, timeframe_id: int, bars: int) -> ServiceResult[list[Candle]]:
        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)
        timeframe = self._timeframe_repo.get_by_id(timeframe_id)
        if timeframe is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)
        exchange = self._exchange_repo.get_by_id(symbol.exchange_id)
        ccxt_id = ccxt_id_for(exchange.name) if exchange else None
        if ccxt_id is None:
            return ServiceResult.fail(code="EXCHANGE_NOT_SUPPORTED_CCXT", http_status=422)

        step_ms = int(timeframe.seconds) * 1000
        now_ms = int(utc_now().timestamp() * 1000)
        since = now_ms - bars * step_ms

        try:
            client = self._client_factory(ccxt_id)
            rows: dict[int, list] = {}
            for _ in range(_MAX_PAGES):
                page = client.fetch_ohlcv(
                    symbol.symbol, timeframe=timeframe.code, since=since, limit=_PAGE_SIZE
                )
                if not page:
                    break
                for row in page:
                    rows[int(row[0])] = row
                last = int(page[-1][0])
                if last + step_ms > now_ms or len(rows) >= bars:
                    break
                since = last + step_ms
        except ccxt.BadSymbol:
            return ServiceResult.fail(code="CCXT_SYMBOL_NOT_FOUND", http_status=422)
        except ccxt.NetworkError:
            return ServiceResult.fail(code="CCXT_NETWORK_ERROR", http_status=503)
        except Exception:
            return ServiceResult.fail(code="CCXT_FETCH_ERROR", http_status=502)

        # Las filas inválidas (high < low, negativos, precios nulos o NaN) se descartan
        candles = [
            candle
            for ts, row in sorted(rows.items())
            # La vela en formación todavía no tiene cierre definitivo
            if ts + step_ms <= now_ms
            and (candle := candle_from_ccxt_row(row, symbol_id, timeframe_id)) is not None
        ]
        return ServiceResult.ok(data=candles[-bars:])
