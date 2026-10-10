# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/bots/routes.py
#
# ENDPOINTS:
# - GET  /bots              → listar bots (admin: todos; user o ?mine=true: los suyos)
# - POST /bots              → crear bot
# - GET  /bots/{id}         → detalle de un bot
# - PUT  /bots/{id}         → renombrar (siempre) o actualizar config (si stopped)
# - POST /bots/{id}/start   → iniciar bot  (stopped  → running)
# - POST /bots/{id}/stop    → detener bot  (running/paused → stopped)
# - POST /bots/{id}/pause   → pausar bot   (running → paused)
#
# NOTAS:
# - En la UI los bots se llaman "agentes"; los mensajes usan esa palabra.
# - Un usuario solo ve y opera bots de sus cuentas (`owner_id`); para un
#   bot ajeno la respuesta es 404, igual que si no existiera.
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.providers import BotServiceFactory, get_bot_factory

from .error_messages import BOT_ERROR_MESSAGES
from .schemas import CreateBotRequest, UpdateBotRequest

router = APIRouter(prefix="/bots", tags=["Bots"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> BotServiceFactory:
    return get_bot_factory(db)


def owner_scope(identity: dict) -> int | None:
    """user_id del que llama, o None si es admin (sin restricción de propiedad)."""
    if int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID):
        return None
    return int(identity["user_id"])


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
        "started_at":     b.started_at.isoformat() if b.started_at else None,
        "stopped_at":     b.stopped_at.isoformat() if b.stopped_at else None,
        "created_at":     b.created_at.isoformat() if b.created_at else None,
    }


# ======================================================================
# GET /bots
# ======================================================================

@router.get("", status_code=200)
def list_bots(
    account_id: int | None = Query(default=None, gt=0),
    mine: bool = Query(default=False, description="Solo los bots de mis cuentas (también para admin)."),
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """
    Lista bots.
    - Admin: todos, o los de `account_id`; con `mine=true`, solo los suyos.
    - Usuario: los de sus cuentas, o los de `account_id` si es suya.
    """
    owner_id = int(identity["user_id"]) if mine else owner_scope(identity)
    result = factory.list_bots().list(account_id=account_id, owner_id=owner_id)
    return build_list_response(
        items=[_bot_to_dict(b) for b in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /bots
# ======================================================================

@router.post("", status_code=201)
def create_bot(
    payload: CreateBotRequest,
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Crea un nuevo bot. Disponible para todos los usuarios autenticados."""
    result = factory.create_bot().create(
        name=payload.name,
        strategy_id=payload.strategy_id,
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        account_id=payload.account_id,
        feature_set_id=payload.feature_set_id,
        mode=payload.mode,
        risk_params=payload.risk_params,
        owner_id=owner_scope(identity),
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
    result = factory.get_bot().get(bot_id=bot_id, owner_id=owner_scope(identity))

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
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Renombra un bot (en cualquier estado) o cambia su configuración (solo si 'stopped')."""
    result = factory.update_bot().update(
        bot_id=bot_id,
        name=payload.name,
        mode=payload.mode,
        risk_params=payload.risk_params,
        owner_id=owner_scope(identity),
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
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Inicia un bot (stopped → running)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="running", owner_id=owner_scope(identity)
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
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Detiene un bot (running/paused → stopped)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="stopped", owner_id=owner_scope(identity)
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
    identity: dict = Depends(token_required_actual),
    factory: BotServiceFactory = Depends(get_factory),
):
    """Pausa un bot (running → paused)."""
    result = factory.update_bot_status().transition(
        bot_id=bot_id, new_status="paused", owner_id=owner_scope(identity)
    )

    if not result.success:
        return build_error_response(result, BOT_ERROR_MESSAGES)

    return build_success_response(data=_bot_to_dict(result.data), msg="Agente pausado.")
