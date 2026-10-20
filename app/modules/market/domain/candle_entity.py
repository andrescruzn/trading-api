# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/candle_entity.py
#
# Entidad de dominio: Candle (vela OHLCV).
#
# NOTAS:
# - Un exchange puede devolver precios nulos o NaN en una vela sin datos.
#   Esas filas se descartan (`candle_from_ccxt_row` → None,
#   `is_valid_ohlcv` → False) en lugar de lanzar `InvalidOperation`, que
#   tumbaría la descarga entera del par.
# ======================================================================

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


class Candle:
    """
    Entidad de dominio: Candle (OHLCV).

    Representa una vela de precio para un símbolo y timeframe dado.
    Los precios y volumen usan Decimal para precisión financiera.
    """

    def __init__(
        self,
        id: int,
        symbol_id: int,
        timeframe_id: int,
        ts: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.symbol_id = symbol_id
        self.timeframe_id = timeframe_id
        self.ts = ts
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.created_at = created_at

    def is_valid_ohlcv(self) -> bool:
        """
        Regla de negocio: valores finitos, high >= low, todos los precios
        >= 0, volumen >= 0.
        """
        values = (self.open, self.high, self.low, self.close, self.volume)
        if not all(_is_finite(v) for v in values):
            # NaN en una comparación de orden de Decimal lanza InvalidOperation
            return False
        return (
            self.high >= self.low
            and self.open >= Decimal("0")
            and self.high >= Decimal("0")
            and self.low >= Decimal("0")
            and self.close >= Decimal("0")
            and self.volume >= Decimal("0")
        )


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(value)
    except (TypeError, ValueError):
        return False


def candle_from_ccxt_row(row: list, symbol_id: int, timeframe_id: int) -> Candle | None:
    """
    Fila OHLCV de ccxt `[ts_ms, open, high, low, close, volume]` → Candle.

    Devuelve None si la fila no se puede convertir (precio nulo, texto) o
    no pasa `is_valid_ohlcv()`. Un volumen nulo cuenta como 0.
    """
    try:
        candle = Candle(
            id=0,
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            ts=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=Decimal(str(row[5])) if row[5] is not None else Decimal("0"),
        )
    except (InvalidOperation, TypeError, ValueError, IndexError, OverflowError, OSError):
        return None
    return candle if candle.is_valid_ohlcv() else None
