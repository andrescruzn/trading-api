# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/rest/candle_features/routes.py
#
# ENDPOINTS:
# - GET  /candle-features            → consulta features (autenticado)
# - POST /candle-features/calculate  → calcula y persiste (solo admin)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.features.providers import FeatureServiceFactory

from .error_messages import CANDLE_FEATURE_ERROR_MESSAGES
from .schemas import CalculateFeaturesRequest

router = APIRouter(prefix="/candle-features", tags=["Features — Candle Features"])


def get_factory(db: Session = Depends(get_db)) -> FeatureServiceFactory:
    return FeatureServiceFactory(session=db)


def _cf_to_dict(cf: Any) -> dict:
    return {
        "id": cf.id,
        "symbol_id": cf.symbol_id,
        "timeframe_id": cf.timeframe_id,
        "ts": cf.ts.isoformat() if cf.ts else None,
        "feature_set_id": cf.feature_set_id,
        "features": cf.features,
    }


# ======================================================================
# GET /candle-features
# ======================================================================

@router.get("", status_code=200)
def list_candle_features(
    symbol_id: int = Query(description="ID del símbolo"),
    timeframe_id: int = Query(description="ID del timeframe"),
    feature_set_id: int = Query(description="ID del feature set"),
    from_ts: Optional[datetime] = Query(default=None, description="Fecha inicio (ISO 8601)"),
    to_ts: Optional[datetime] = Query(default=None, description="Fecha fin (ISO 8601)"),
    limit: int = Query(default=500, ge=1, le=1000),
    _identity: dict = Depends(token_required_actual),
    factory: FeatureServiceFactory = Depends(get_factory),
):
    """Consulta features calculadas. Retorna orden descendente por ts."""
    result = factory.list_candle_features().list(
        symbol_id=symbol_id,
        timeframe_id=timeframe_id,
        feature_set_id=feature_set_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )
    if not result.success:
        return build_error_response(result, CANDLE_FEATURE_ERROR_MESSAGES)

    return build_list_response(
        items=[_cf_to_dict(cf) for cf in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /candle-features/calculate
# ======================================================================

@router.post("/calculate", status_code=200)
def calculate_features(
    payload: CalculateFeaturesRequest,
    _identity: dict = Depends(admin_required),
    factory: FeatureServiceFactory = Depends(get_factory),
):
    """
    Calcula RSI, EMA, MACD, ATR, Bollinger Bands y régimen de mercado
    para las velas del rango especificado y los persiste en candle_features.
    Solo admins.
    """
    result = factory.calculate_features().calculate(
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        feature_set_id=payload.feature_set_id,
        from_ts=payload.from_ts,
        to_ts=payload.to_ts,
    )
    if not result.success:
        return build_error_response(result, CANDLE_FEATURE_ERROR_MESSAGES)

    d = result.data
    return build_success_response(
        data=d,
        msg=f"{d['rows_calculated']} features calculadas ({d['rows_affected']} filas afectadas).",
    )
