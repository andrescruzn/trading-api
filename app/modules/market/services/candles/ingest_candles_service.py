# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository


@dataclass(frozen=True)
class CandleInputRow:
    """DTO: una fila de vela para ingestar."""
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class IngestPayload:
    """Resultado de una ingestión de velas."""
    symbol_id: int
    timeframe_id: int
    rows_received: int
    rows_affected: int


class IngestCandlesService:
    """
    Ingesta velas OHLCV en lote para un símbolo y timeframe.

    Usa INSERT ... ON DUPLICATE KEY UPDATE para manejar duplicados.
    Valida que el símbolo y timeframe existan antes de insertar.
    """

    def __init__(
        self,
        candle_repo: CandleRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        session: Session,
    ):
        self._candle_repo = candle_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._session = session

    def ingest(
        self,
        symbol_id: int,
        timeframe_id: int,
        rows: list[dict[str, Any]],
    ) -> ServiceResult[IngestPayload]:
        # Validar que el símbolo existe
        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        # Validar que el timeframe existe
        tf = self._timeframe_repo.get_by_id(timeframe_id)
        if tf is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)

        if not rows:
            return ServiceResult.fail(code="CANDLES_EMPTY_PAYLOAD", http_status=422)

        # Construir entidades Candle validando OHLCV
        candles: list[Candle] = []
        for i, row in enumerate(rows):
            try:
                candle = Candle(
                    id=0,
                    symbol_id=symbol_id,
                    timeframe_id=timeframe_id,
                    ts=row["ts"],
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row.get("volume", 0))),
                )
            except (KeyError, Exception):
                return ServiceResult.fail(
                    code="CANDLES_INVALID_ROW",
                    http_status=422,
                    meta={"row_index": i},
                )

            if not candle.is_valid_ohlcv():
                return ServiceResult.fail(
                    code="CANDLES_INVALID_OHLCV",
                    http_status=422,
                    meta={"row_index": i},
                )
            candles.append(candle)

        rows_affected = self._candle_repo.bulk_upsert(candles)
        self._session.commit()

        return ServiceResult.ok(
            data=IngestPayload(
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                rows_received=len(candles),
                rows_affected=rows_affected,
            )
        )
