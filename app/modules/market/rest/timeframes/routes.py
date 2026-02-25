# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/timeframes/routes.py
#
# ENDPOINTS:
# - GET  /timeframes        → lista todos (autenticado)
# - POST /timeframes        → crear (solo admin)
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_list_response,
    build_created_response,
)
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.market.providers import MarketServiceFactory

from .error_messages import TIMEFRAME_ERROR_MESSAGES
from .schemas import CreateTimeframeRequest

router = APIRouter(prefix="/timeframes", tags=["Market — Timeframes"])


def get_factory(db: Session = Depends(get_db)) -> MarketServiceFactory:
    return MarketServiceFactory(session=db)


def _tf_to_dict(tf: Any) -> dict:
    return {"id": tf.id, "code": tf.code, "seconds": tf.seconds}


# ======================================================================
# GET /timeframes
# ======================================================================

@router.get("", status_code=200)
def list_timeframes(
    _identity: dict = Depends(token_required_actual),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Lista timeframes ordenados por duración. Cualquier usuario autenticado."""
    result = factory.list_timeframes().list()

    if not result.success:
        return build_error_response(result, TIMEFRAME_ERROR_MESSAGES)

    return build_list_response(
        items=[_tf_to_dict(tf) for tf in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /timeframes
# ======================================================================

@router.post("", status_code=201)
def create_timeframe(
    payload: CreateTimeframeRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Crea un timeframe. Solo admins."""
    result = factory.create_timeframe().create(
        code=payload.code,
        seconds=payload.seconds,
    )

    if not result.success:
        return build_error_response(result, TIMEFRAME_ERROR_MESSAGES)

    return build_created_response(
        data=_tf_to_dict(result.data),
        msg="Timeframe creado exitosamente.",
    )
