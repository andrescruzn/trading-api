# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/candles/routes.py
#
# ENDPOINTS:
# - GET  /candles                → consulta (autenticado, filtros)
# - POST /candles/ingest         → ingestión masiva (solo admin)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_list_response,
    build_success_response,
)
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.market.providers import MarketServiceFactory

from .error_messages import CANDLE_ERROR_MESSAGES
from .schemas import IngestCandlesRequest, FetchCandlesRequest

router = APIRouter(prefix="/candles", tags=["Market — Candles"])


def get_factory(db: Session = Depends(get_db)) -> MarketServiceFactory:
    return MarketServiceFactory(session=db)


def _candle_to_dict(c: Any) -> dict:
    return {
        "id": c.id,
        "symbol_id": c.symbol_id,
        "timeframe_id": c.timeframe_id,
        "ts": c.ts.isoformat() if c.ts else None,
        "open": str(c.open),
        "high": str(c.high),
        "low": str(c.low),
        "close": str(c.close),
        "volume": str(c.volume),
    }


# ======================================================================
# GET /candles
# ======================================================================

@router.get("", status_code=200)
def list_candles(
    symbol_id: int = Query(description="ID del símbolo"),
    timeframe_id: int = Query(description="ID del timeframe"),
    from_ts: Optional[datetime] = Query(default=None, description="Fecha inicio (ISO 8601)"),
    to_ts: Optional[datetime] = Query(default=None, description="Fecha fin (ISO 8601)"),
    limit: int = Query(default=500, ge=1, le=1000, description="Máximo de velas a retornar"),
    _identity: dict = Depends(token_required_actual),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """
    Consulta velas OHLCV. Las velas se retornan ordenadas de más reciente a más antigua.
    Cualquier usuario autenticado puede consultarlas.
    """
    result = factory.list_candles().list(
        symbol_id=symbol_id,
        timeframe_id=timeframe_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )

    if not result.success:
        return build_error_response(result, CANDLE_ERROR_MESSAGES)

    return build_list_response(
        items=[_candle_to_dict(c) for c in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /candles/ingest
# ======================================================================

@router.post("/ingest", status_code=200)
def ingest_candles(
    payload: IngestCandlesRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """
    Ingesta masiva de velas OHLCV (máx 5000 por petición).
    Si una vela ya existe (symbol_id + timeframe_id + ts), se actualiza.
    Solo admins.
    """
    rows = [
        {
            "ts": row.ts,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
        }
        for row in payload.candles
    ]

    result = factory.ingest_candles().ingest(
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        rows=rows,
    )

    if not result.success:
        return build_error_response(result, CANDLE_ERROR_MESSAGES)

    return build_success_response(
        data={
            "symbol_id": result.data.symbol_id,
            "timeframe_id": result.data.timeframe_id,
            "rows_received": result.data.rows_received,
            "rows_affected": result.data.rows_affected,
        },
        msg=f"Ingestión completada: {result.data.rows_affected} filas afectadas.",
    )


# ======================================================================
# POST /candles/fetch  — descarga desde exchange real via ccxt
# ======================================================================

@router.post("/fetch", status_code=200)
def fetch_candles_from_exchange(
    payload: FetchCandlesRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """
    Descarga velas OHLCV desde el exchange real (via ccxt) y las guarda en BD.
    El exchange se resuelve automáticamente desde el símbolo.
    Solo admins.
    """
    result = factory.fetch_candles().fetch(
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        limit=payload.limit,
    )

    if not result.success:
        return build_error_response(result, CANDLE_ERROR_MESSAGES)

    d = result.data
    return build_success_response(
        data=d,
        msg=f"{d['rows_fetched']} velas descargadas de {d['exchange']} ({d['symbol']} {d['timeframe']}).",
    )
