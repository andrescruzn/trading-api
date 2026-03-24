# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/signals/routes.py
#
# ENDPOINTS:
# - GET  /signals              → listar signals de un bot (requiere bot_id)
# - POST /signals/generate     → generar señal invocando el Agente (M6)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.providers import BotServiceFactory, get_bot_factory

from .error_messages import SIGNAL_ERROR_MESSAGES
from .schemas import GenerateSignalRequest

router = APIRouter(prefix="/api/signals", tags=["Signals"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> BotServiceFactory:
    return get_bot_factory(db)


# ======================================================================
# Serializer
# ======================================================================

def _decimal_or_none(val: Decimal | None) -> float | None:
    return float(val) if val is not None else None


def _signal_to_dict(s: Signal) -> dict[str, Any]:
    return {
        "id":            s.id,
        "bot_id":        s.bot_id,
        "ts":            s.ts.isoformat() if s.ts else None,
        "action":        s.action,
        "approved":      s.approved,
        "confidence":    _decimal_or_none(s.confidence),
        "entry_price":   _decimal_or_none(s.entry_price),
        "stop_loss":     _decimal_or_none(s.stop_loss),
        "take_profit":   _decimal_or_none(s.take_profit),
        "position_size": _decimal_or_none(s.position_size),
        "rr_ratio":      _decimal_or_none(s.rr_ratio),
        "reasons":       s.reasons,
        "created_at":    s.created_at.isoformat() if s.created_at else None,
    }


# ======================================================================
# GET /signals
# ======================================================================

@router.get("", status_code=200)
def list_signals(
    bot_id: int = Query(..., gt=0, description="ID del bot propietario de las signals."),
    action: str | None = Query(default=None, description="Filtrar por acción: buy, sell, hold."),
    from_ts: datetime | None = Query(default=None, description="Desde (ISO 8601)."),
    to_ts: datetime | None = Query(default=None, description="Hasta (ISO 8601)."),
    limit: int = Query(default=50, ge=1, le=500),
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Lista signals de un bot con filtros opcionales."""
    result = factory.list_signals().list(
        bot_id=bot_id,
        action=action,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )

    if not result.success:
        return build_error_response(result, SIGNAL_ERROR_MESSAGES)

    return build_list_response(
        items=[_signal_to_dict(s) for s in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /signals/generate
# ======================================================================

@router.post("/generate", status_code=201)
def generate_signal(
    payload: GenerateSignalRequest,
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Genera una señal de trading para el bot indicado invocando el Agente (M6).

    El bot debe estar en estado 'running'.
    La señal se persiste siempre (aprobada o rechazada) para trazabilidad.
    """
    result = factory.generate_signal().generate(bot_id=payload.bot_id)

    if not result.success:
        return build_error_response(result, SIGNAL_ERROR_MESSAGES)

    return build_created_response(
        data=_signal_to_dict(result.data),
        msg="Señal generada exitosamente.",
    )
