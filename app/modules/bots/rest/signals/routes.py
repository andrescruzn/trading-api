# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/signals/routes.py
#
# ENDPOINTS:
# - GET  /signals              → listar signals de un bot (requiere bot_id).
#                                 Con `page` responde paginado {items, pagination}
# - POST /signals/generate     → generar señal invocando el Agente (M6)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.contracts import PageRequest
from app.common.contracts.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_paginated_response,
    send,
)
from app.common.security.jwt import read_scope, super_admin_required, token_required_actual, write_scope
from app.common.security.rate_limiter import agent_analysis_rate_limiter, check_user_rate_limit
from app.extensions.db import get_db
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.providers import BotServiceFactory, get_bot_factory

from app.modules.orders.rest.signal_decisions.error_messages import (
    SIGNAL_DECISION_ERROR_MESSAGES,
)

from .error_messages import SIGNAL_ERROR_MESSAGES
from .schemas import GenerateSignalRequest

router = APIRouter(prefix="/signals", tags=["Signals"])


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
        "id":             s.id,
        "bot_id":         s.bot_id,
        "ts":             s.ts.isoformat() if s.ts else None,
        "action":         s.action,
        "approved":       s.approved,
        "confidence":     _decimal_or_none(s.confidence),
        "entry_price":    _decimal_or_none(s.entry_price),
        "stop_loss":      _decimal_or_none(s.stop_loss),
        "take_profit":    _decimal_or_none(s.take_profit),
        "position_size":  _decimal_or_none(s.position_size),
        "rr_ratio":       _decimal_or_none(s.rr_ratio),
        "llm_provider":   s.llm_provider,
        "llm_model":      s.llm_model,
        "llm_latency_ms": s.llm_latency_ms,
        "reasons":        s.reasons,
        "created_at":     s.created_at.isoformat() if s.created_at else None,
        "decision_status":    s.decision_status,
        "expires_at":         s.expires_at.isoformat() if s.expires_at else None,
        "decided_at":         s.decided_at.isoformat() if s.decided_at else None,
        "decision_channel":   s.decision_channel,
        "decision_reason":    s.decision_reason,
        # Texto de UI del fallo (los códigos se traducen en el backend)
        "decision_reason_message": (
            SIGNAL_DECISION_ERROR_MESSAGES.get(s.decision_reason, s.decision_reason)
            if s.decision_reason else None
        ),
        "candle_ts":          s.candle_ts.isoformat() if s.candle_ts else None,
    }


# ======================================================================
# GET /signals/pending  (antes de cualquier ruta /signals/{id})
# ======================================================================

@router.get("/pending", status_code=200)
def list_pending_signals(
    mine: bool = Query(default=True, description="Solo las de mis agentes (también para admin)."),
    limit: int = Query(default=50, ge=1, le=200),
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Señales que esperan aprobación, con el agente al que pertenecen."""
    owner_id = int(identity["user_id"]) if mine else read_scope(identity)
    result = factory.list_pending_signals().list(owner_id=owner_id, limit=limit)

    if not result.success:
        return build_error_response(result, SIGNAL_ERROR_MESSAGES)

    return build_list_response(
        items=[
            {
                **_signal_to_dict(item.signal),
                "bot_name": item.bot.name,
                "bot_mode": item.bot.mode,
            }
            for item in result.data
        ],
        msg="OK",
    )


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
    page: int | None = Query(default=None, ge=1, description="Activa la respuesta paginada."),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Lista signals de un bot con filtros opcionales (la más reciente primero).
    Sin `page`: `data` es la lista (hasta `limit`). Con `page`: `data` es
    `{items, pagination}` y `limit` se ignora.
    """
    if page is not None:
        page_result = factory.list_signals().list_page(
            bot_id=bot_id,
            page=PageRequest.of(page, page_size),
            action=action,
            from_ts=from_ts,
            to_ts=to_ts,
            owner_id=read_scope(identity),
        )
        if not page_result.success:
            return build_error_response(page_result, SIGNAL_ERROR_MESSAGES)
        return build_paginated_response(
            items=[_signal_to_dict(s) for s in page_result.data.items],
            total=page_result.data.total,
            page=page_result.data.page,
            page_size=page_result.data.page_size,
        )

    result = factory.list_signals().list(
        bot_id=bot_id,
        action=action,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        owner_id=read_scope(identity),
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
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Genera una señal de trading para el bot indicado invocando el Agente (M6).

    El bot debe estar en estado 'running'.
    La señal se persiste siempre (aprobada o rechazada) para trazabilidad.
    """
    # Cada análisis es una llamada de pago al LLM: límite por usuario
    check_user_rate_limit(agent_analysis_rate_limiter, identity["user_id"])

    result = factory.generate_signal().generate(
        bot_id=payload.bot_id, owner_id=write_scope(identity)
    )

    if not result.success:
        return build_error_response(result, SIGNAL_ERROR_MESSAGES)

    return build_created_response(
        data=_signal_to_dict(result.data),
        msg="Señal generada exitosamente.",
    )
