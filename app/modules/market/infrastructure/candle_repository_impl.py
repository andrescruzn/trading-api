# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/candle_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de candles (OHLCV).
# Usa INSERT ... ON DUPLICATE KEY UPDATE para bulk upsert eficiente.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.infrastructure.candle_model import CandleModel


class SqlAlchemyCandleRepository(CandleRepository):
    """Repositorio concreto de candles usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _as_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
        """Normaliza datetime naive a UTC aware (MySQL devuelve naive)."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _to_domain(model: CandleModel) -> Candle:
        return Candle(
            id=model.id,
            symbol_id=model.symbol_id,
            timeframe_id=model.timeframe_id,
            ts=SqlAlchemyCandleRepository._as_utc_aware(model.ts),  # type: ignore[arg-type]
            open=Decimal(str(model.open)),
            high=Decimal(str(model.high)),
            low=Decimal(str(model.low)),
            close=Decimal(str(model.close)),
            volume=Decimal(str(model.volume)),
            created_at=SqlAlchemyCandleRepository._as_utc_aware(model.created_at),
        )

    # ==================================================================
    # Contract
    # ==================================================================

    def list_candles(
        self,
        symbol_id: int,
        timeframe_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[Candle]:
        query = (
            self._session.query(CandleModel)
            .filter(
                CandleModel.symbol_id == symbol_id,
                CandleModel.timeframe_id == timeframe_id,
            )
        )
        if from_ts is not None:
            query = query.filter(CandleModel.ts >= from_ts)
        if to_ts is not None:
            query = query.filter(CandleModel.ts <= to_ts)

        query = query.order_by(CandleModel.ts.desc()).limit(limit)
        return [self._to_domain(m) for m in query.all()]

    def bulk_upsert(self, candles: list[Candle]) -> int:
        """
        Inserta o actualiza velas usando INSERT ... ON DUPLICATE KEY UPDATE.

        La tabla tiene UNIQUE KEY (symbol_id, timeframe_id, ts), por lo que
        los duplicados se actualizan con los nuevos datos OHLCV.
        """
        if not candles:
            return 0

        rows = []
        for c in candles:
            # Convertir ts a naive UTC para MySQL (TIMESTAMP no lleva tzinfo)
            ts_naive = c.ts.replace(tzinfo=None) if c.ts.tzinfo else c.ts
            rows.append({
                "symbol_id": c.symbol_id,
                "timeframe_id": c.timeframe_id,
                "ts": ts_naive,
                "open": str(c.open),
                "high": str(c.high),
                "low": str(c.low),
                "close": str(c.close),
                "volume": str(c.volume),
            })

        stmt = text(
            """
            INSERT INTO candles (symbol_id, timeframe_id, ts, open, high, low, close, volume)
            VALUES (:symbol_id, :timeframe_id, :ts, :open, :high, :low, :close, :volume)
            ON DUPLICATE KEY UPDATE
                open   = VALUES(open),
                high   = VALUES(high),
                low    = VALUES(low),
                close  = VALUES(close),
                volume = VALUES(volume)
            """
        )

        result = self._session.execute(stmt, rows)
        return result.rowcount
