# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/candle_entity.py
#
# Entidad de dominio: Candle (vela OHLCV).
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional


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
        Regla de negocio: high >= low, todos los precios >= 0, volumen >= 0.
        """
        return (
            self.high >= self.low
            and self.open >= Decimal("0")
            and self.high >= Decimal("0")
            and self.low >= Decimal("0")
            and self.close >= Decimal("0")
            and self.volume >= Decimal("0")
        )
