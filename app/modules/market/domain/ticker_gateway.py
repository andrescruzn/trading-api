# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/ticker_gateway.py
#
# Contrato para leer las estadísticas de 24 h de un mercado (ticker):
# precio actual, variación, volumen, máximo y mínimo.
# Implementado en infrastructure/ccxt_ticker_gateway.py (ccxt, Binance).
#
# DECISIÓN:
# - Son datos de vista (el explorador), no se guardan en la BD.
# - `fetch` nunca falla hacia el servicio: si el exchange no responde,
#   devuelve un dict vacío y el ranking se muestra sin datos en vivo.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Ticker:
    """Estadísticas de las últimas 24 h de un símbolo."""

    symbol: str
    last: float | None
    change_24h: float | None        # fracción: 0.025 = +2,5 %
    quote_volume_24h: float | None  # volumen en la moneda de cotización (USDT)
    high_24h: float | None
    low_24h: float | None
    ts: datetime | None


class TickerGateway(Protocol):
    def fetch(self, symbols: list[str]) -> dict[str, Ticker]:
        """Tickers por símbolo; los que no se pudieron leer no aparecen."""
        ...
