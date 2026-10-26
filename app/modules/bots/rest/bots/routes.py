# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/bots/routes.py
#
# ENDPOINTS:
# - GET  /bots              → listar bots (admin: todos; user o ?mine=true: los suyos).
#                              Con `page` responde paginado {items, pagination}
# - GET  /bots/shared       → agentes que comparten sus señales (vista pública)
# - POST /bots              → crear bot
# - GET  /bots/{id}         → detalle de un bot
# - PUT  /bots/{id}         → renombrar (siempre) o actualizar config (si stopped)
# - POST /bots/{id}/start   → iniciar bot  (stopped  → running)
# - POST /bots/{id}/stop    → detener bot  (running/paused → stopped)
# - POST /bots/{id}/pause   → pausar bot   (running → paused)
# - POST /bots/{id}/market/sync → descargar velas y recalcular indicadores
# - POST   /bots/{id}/subscription → seguir las señales de un agente compartido
# - DELETE /bots/{id}/subscription → dejar de seguirlas
#
# NOTAS:
# - En la UI los bots se llaman "agentes"; los mensajes usan esa palabra.
# - Agentes reales (`mode=live`, billetera de Binance) y demo (`mode=paper`,
#   dinero simulado con `demo_capital`) conviven: Inicio lista los reales y
#   "Agentes demo" los demo, con el filtro `mode`.
# - Un usuario solo ve y opera bots de sus cuentas (`owner_id`); para un
#   bot ajeno la respuesta es 404, igual que si no existiera.
# - `GET /bots/shared` va antes de `GET /bots/{bot_id}`: si no, "shared"
#   se intentaría leer como bot_id (422).
# ======================================================================

from __future__ import annotations

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
    build_success_response,
)
from app.common.security.jwt import read_scope, super_admin_required, token_required_actual, write_scope
from app.common.security.rate_limiter import check_user_rate_limit, market_sync_rate_limiter
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.providers import BotServiceFactory, get_bot_factory
from app.modules.bots.services.subscriptions import SharedBot, SubscriptionState

from .error_messages import BOT_ERROR_MESSAGES
from .schemas import CreateBotRequest, UpdateBotRequest

router = APIRouter(prefix="/bots", tags=["Bots"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> BotServiceFactory:
    return get_bot_factory(db)


# ======================================================================
# Serializer
# ======================================================================

def _bot_to_dict(b: Bot) -> dict[str, Any]:
    return {
        "id":             b.id,
        "name":           b.name,
        "strategy_id":    b.strategy_id,
        "symbol_id":      b.symbol_id,
        "timeframe_id":   b.timeframe_id,
        "account_id":     b.account_id,
        "feature_set_id": b.feature_set_id,
        "mode":           b.mode,
        "status":         b.status,
        "risk_params":    b.risk_params,
        "execution_mode": b.execution_mode,
        "approval_ttl_minutes": b.approval_ttl_minutes,
        "share_signals":  b.share_signals,
        "demo_capital":   None if b.demo_capital is None else str(b.demo_capital),
        "started_at":     to_iso_utc(b.started_at),
        "stopped_at":     to_iso_utc(b.stopped_at),
        "created_at":     to_iso_utc(b.created_at),
    }


def _shared_bot_to_dict(s: SharedBot) -> dict[str, Any]:
    return {
        "id":                s.bot_id,
        "strategy_id":       s.strategy_id,
        "strategy_name":     s.strategy_name,
        "symbol_id":         s.symbol_id,
        "symbol":            s.symbol,
        "timeframe_id":      s.timeframe_id,
        "timeframe":         s.timeframe,
        "mode":              s.mode,
        "status":            s.status,
        "subscribers_count": s.subscribers_count,
        "is_subscribed":     s.is_subscribed,
        "is_mine":           s.is_mine,
    }


def _subscription_to_dict(s: SubscriptionState) -> dict[str, Any]:
    return {
        "bot_id":            s.bot_id,
        "is_subscribed":     s.is_subscribed,
        "subscribers_count": s.subscribers_count,
    }


# ======================================================================
# GET /bots
# ======================================================================

@router.get("", status_code=200)
def list_bots(
    account_id: int | None = Query(default=None, gt=0),
    mine: bool = Query(default=False, description="Solo los bots de mis cuentas (también para admin)."),
    status: str | None = Query(default=None, description="running | paused | stopped | error"),
    mode: str | None = Query(default=None, description="paper | live"),
    user_id: int | None = Query(default=None, gt=0, description="Solo admin: dueño de las cuentas."),
    page: int | None = Query(default=None, ge=1, description="Activa la respuesta paginada."),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Lista bots (el más reciente primero).
    - Admin: todos, o los de `account_id` o del dueño `user_id`; con `mine=true`, solo los suyos.
    - Usuario: los de sus cuentas, o los de `account_id` si es suya.
    - Sin `page`: `data` es la lista completa. Con `page`: `data` es `{items, pagination}`.
    """
    filters = {
        "account_id": account_id,
        "owner_id":   int(identity["user_id"]) if mine else read_scope(identity),
        "status":     status,
        "mode":       mode,
        "user_id":    user_id,
    }
    service = factory.list_bots()

    if page is not None:
        result = service.list_page(page=PageRequest.of(page, page_size), **filters)
        if not result.success:
            return build_error_response(result, BOT_ERROR_MESSAGES)
        return build_paginated_response(
            items=[_bot_to_dict(b) for b in result.data.items],
            total=result.data.total,
            page=result.data.page,
            page_size=result.data.page_size,
        )

    result = service.list(**filters)
    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)
    return build_list_response(
        items=[_bot_to_dict(b) for b in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# GET /bots/shared   (antes de /bots/{bot_id})
# ======================================================================

@router.get("/shared", status_code=200)
def list_shared_bots(
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Agentes que comparten sus señales, sin datos de la cuenta ni del dueño.
    Incluye si el usuario ya los sigue (`is_subscribed`) y si son suyos (`is_mine`).
    """
    result = factory.list_shared_bots().list(user_id=int(identity["user_id"]))
    return build_list_response(
        items=[_shared_bot_to_dict(s) for s in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /bots
# ======================================================================

@router.post("", status_code=201)
def create_bot(
    payload: CreateBotRequest,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Crea un agente real (billetera de Binance) o demo (dinero simulado). Solo super admin."""
    result = factory.create_bot().create(
        name=payload.name,
        strategy_id=payload.strategy_id,
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        feature_set_id=payload.feature_set_id,
        mode=payload.mode,
        risk_params=payload.risk_params,
        requester_user_id=int(identity["user_id"]),
        demo_capital=payload.demo_capital,
        execution_mode=payload.execution_mode,
        approval_ttl_minutes=payload.approval_ttl_minutes,
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_created_response(
        data=_bot_to_dict(result.data),
        msg="Agente creado.",
    )


# ======================================================================
# GET /bots/{bot_id}
# ======================================================================

@router.get("/{bot_id}", status_code=200)
def get_bot(
    bot_id: int,
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Obtiene el detalle de un bot por ID."""
    result = factory.get_bot().get(bot_id=bot_id, owner_id=read_scope(identity))

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=_bot_to_dict(result.data), msg="OK")


# ======================================================================
# PUT /bots/{bot_id}
# ======================================================================

@router.put("/{bot_id}", status_code=200)
def update_bot(
    bot_id: int,
    payload: UpdateBotRequest,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Renombra un bot o cambia su modo de ejecución (en cualquier estado), o
    cambia su riesgo (solo si 'stopped'). Real o demo no se cambia.
    """
    result = factory.update_bot().update(
        bot_id=bot_id,
        name=payload.name,
        risk_params=payload.risk_params,
        owner_id=write_scope(identity),
        execution_mode=payload.execution_mode,
        approval_ttl_minutes=payload.approval_ttl_minutes,
        clear_approval_ttl="approval_ttl_minutes" in payload.model_fields_set
        and payload.approval_ttl_minutes is None,
        share_signals=payload.share_signals,
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(
        data=_bot_to_dict(result.data),
        msg="Agente actualizado.",
    )


# ======================================================================
# POST /bots/{bot_id}/start
# ======================================================================

@router.post("/{bot_id}/start", status_code=200)
def start_bot(
    bot_id: int,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Inicia un bot (stopped → running)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="running", owner_id=write_scope(identity)
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=_bot_to_dict(result.data), msg="Agente iniciado.")


# ======================================================================
# POST /bots/{bot_id}/stop
# ======================================================================

@router.post("/{bot_id}/stop", status_code=200)
def stop_bot(
    bot_id: int,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Detiene un bot (running/paused → stopped)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="stopped", owner_id=write_scope(identity)
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=_bot_to_dict(result.data), msg="Agente detenido.")


# ======================================================================
# POST /bots/{bot_id}/pause
# ======================================================================

@router.post("/{bot_id}/pause", status_code=200)
def pause_bot(
    bot_id: int,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Pausa un bot (running → paused)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="paused", owner_id=write_scope(identity)
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=_bot_to_dict(result.data), msg="Agente pausado.")


# ======================================================================
# POST /bots/{bot_id}/market/sync
# ======================================================================

@router.post("/{bot_id}/market/sync", status_code=200)
def sync_bot_market_data(
    bot_id: int,
    identity: dict = Depends(super_admin_required),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Descarga las velas del agente y recalcula sus indicadores."""
    # Cada llamada pega al exchange: límite por usuario
    check_user_rate_limit(market_sync_rate_limiter, identity["user_id"])

    result = factory.sync_bot_market_data().sync(
        bot_id=bot_id, owner_id=write_scope(identity)
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=result.data, msg="Datos del agente actualizados.")


# ======================================================================
# POST /bots/{bot_id}/subscription
# ======================================================================

@router.post("/{bot_id}/subscription", status_code=200)
def subscribe_to_bot(
    bot_id: int,
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Sigue las señales de un agente compartido (idempotente; exige Telegram)."""
    result = factory.subscribe_to_bot().subscribe(
        bot_id=bot_id, user_id=int(identity["user_id"])
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(
        data=_subscription_to_dict(result.data),
        msg="Listo: te llegarán por Telegram las señales de este agente.",
    )


# ======================================================================
# DELETE /bots/{bot_id}/subscription
# ======================================================================

@router.delete("/{bot_id}/subscription", status_code=200)
def unsubscribe_from_bot(
    bot_id: int,
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Deja de seguir las señales de un agente (idempotente)."""
    result = factory.unsubscribe_from_bot().unsubscribe(
        bot_id=bot_id, user_id=int(identity["user_id"])
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(
        data=_subscription_to_dict(result.data),
        msg="Ya no recibirás las señales de este agente.",
    )
