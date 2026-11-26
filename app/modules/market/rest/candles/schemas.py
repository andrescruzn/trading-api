# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CandleRowRequest(BaseModel):
    """Una fila OHLCV para ingestión."""
    ts: datetime
    open: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    low: Decimal = Field(ge=0)
    close: Decimal = Field(ge=0)
    volume: Decimal = Field(default=Decimal("0"), ge=0)


class IngestCandlesRequest(BaseModel):
    """Payload de ingestión masiva de velas."""
    symbol_id: int = Field(ge=1)
    timeframe_id: int = Field(ge=1)
    candles: list[CandleRowRequest] = Field(min_length=1, max_length=5000)


class FetchCandlesRequest(BaseModel):
    """Descarga velas desde un exchange real via ccxt."""
    symbol_id: int = Field(ge=1)
    timeframe_id: int = Field(ge=1)
    limit: int = Field(default=500, ge=1, le=1000)
