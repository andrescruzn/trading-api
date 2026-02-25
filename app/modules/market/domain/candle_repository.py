# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/candle_repository.py
#
# Contrato (interfaz) del repositorio de candles (OHLCV).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.modules.market.domain.candle_entity import Candle


class CandleRepository(ABC):

    @abstractmethod
    def list_candles(
        self,
        symbol_id: int,
        timeframe_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[Candle]: ...

    @abstractmethod
    def bulk_upsert(self, candles: list[Candle]) -> int:
        """
        Inserta o actualiza velas en lote.
        Retorna el número de filas afectadas.
        """
        ...
