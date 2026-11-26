# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/ccxt_ticker_gateway.py
#
# Implementación ccxt de TickerGateway: estadísticas de 24 h de Binance
# (datos públicos, sin API key).
#
# DECISIONES:
# - Un solo cliente ccxt por proceso: `load_markets` de Binance (spot +
#   futuros) son varias peticiones lentas y no tiene sentido repetirlas en
#   cada carga de la página.
# - Spot y perpetuos (`XAU/USDT:USDT`) van en llamadas separadas: ccxt
#   rechaza mezclar tipos de mercado en un mismo `fetch_tickers`.
# - Caché en memoria por símbolo durante EXPLORER_TICKERS_TTL_SECONDS:
#   varias personas mirando el explorador no multiplican las llamadas.
# - Siempre producción (nunca sandbox): son precios públicos de referencia.
# - Un fallo del exchange se registra en el log y deja ese grupo sin datos;
#   nunca tumba el ranking.
# ======================================================================

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

import ccxt

from app.common.config import settings
from app.modules.market.domain.ccxt_exchanges import is_perpetual
from app.modules.market.domain.ticker_gateway import Ticker

logger = logging.getLogger(__name__)

_client: Any | None = None
_client_lock = threading.Lock()

# símbolo → (instante monotónico de lectura, ticker)
_cache: dict[str, tuple[float, Ticker]] = {}
_cache_lock = threading.Lock()


def _get_client() -> Any:
    global _client
    with _client_lock:
        if _client is None:
            _client = ccxt.binance({"enableRateLimit": True})
        return _client


class CcxtTickerGateway:
    """Tickers de 24 h de Binance con caché corta en memoria."""

    def __init__(self, ttl_seconds: int | None = None):
        self._ttl = ttl_seconds if ttl_seconds is not None else settings.EXPLORER_TICKERS_TTL_SECONDS

    def fetch(self, symbols: list[str]) -> dict[str, Ticker]:
        now = time.monotonic()
        result: dict[str, Ticker] = {}
        missing: list[str] = []

        with _cache_lock:
            for symbol in dict.fromkeys(symbols):
                cached = _cache.get(symbol)
                if cached is not None and now - cached[0] < self._ttl:
                    result[symbol] = cached[1]
                else:
                    missing.append(symbol)

        if not missing:
            return result

        spot = [s for s in missing if not is_perpetual(s)]
        perpetual = [s for s in missing if is_perpetual(s)]
        fetched: dict[str, Ticker] = {}
        for group in (spot, perpetual):
            if group:
                fetched.update(self._fetch_group(group))

        with _cache_lock:
            for symbol, ticker in fetched.items():
                _cache[symbol] = (now, ticker)

        result.update(fetched)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_group(self, symbols: list[str]) -> dict[str, Ticker]:
        try:
            client = _get_client()
            markets = client.load_markets()
            # Un símbolo que Binance ya no lista haría fallar todo el lote
            known = [s for s in symbols if s in markets]
            if not known:
                return {}
            raw = client.fetch_tickers(known)
        except Exception as exc:  # noqa: BLE001 — cualquier fallo deja el grupo sin datos
            logger.warning("[explorer] no se pudieron leer los tickers (%s): %s", symbols[0], exc)
            return {}

        tickers: dict[str, Ticker] = {}
        for symbol in known:
            data = raw.get(symbol)
            if data:
                tickers[symbol] = _to_ticker(symbol, data)
        return tickers


def _to_ticker(symbol: str, data: dict[str, Any]) -> Ticker:
    percentage = _to_float(data.get("percentage"))
    timestamp = data.get("timestamp")
    return Ticker(
        symbol=symbol,
        last=_to_float(data.get("last")) or _to_float(data.get("close")),
        # ccxt da `percentage` en % (2.5 = +2,5 %); el resto de la API usa fracciones
        change_24h=percentage / 100 if percentage is not None else None,
        quote_volume_24h=_to_float(data.get("quoteVolume")),
        high_24h=_to_float(data.get("high")),
        low_24h=_to_float(data.get("low")),
        ts=datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc) if timestamp else None,
    )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
