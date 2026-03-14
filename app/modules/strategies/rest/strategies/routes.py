# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/strategies/routes.py
#
# ENDPOINTS:
# - GET  /strategies              → listar todas (cualquier usuario)
# - POST /strategies              → crear (admin)
# - GET  /strategies/{id}         → obtener por ID (cualquier usuario)
# - PUT  /strategies/{id}         → actualizar (admin)
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import (
    build_error_response,
    build_list_response,
    build_created_response,
    build_success_response,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.providers import StrategyServiceFactory

from .error_messages import STRATEGY_ERROR_MESSAGES
from .schemas import CreateStrategyRequest, UpdateStrategyRequest

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> StrategyServiceFactory:
    return StrategyServiceFactory(session=db)


# ======================================================================
# Serializer
# ======================================================================

def _strategy_to_dict(s: Strategy) -> dict[str, Any]:
    return {
        "id":          s.id,
        "name":        s.name,
        "version":     s.version,
        "description": s.description,
        "parameters":  s.parameters,
        "created_at":  s.created_at.isoformat() if s.created_at else None,
    }


# ======================================================================
# GET /strategies
# ======================================================================

@router.get("", status_code=200)
def list_strategies(
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Lista todas las estrategias. Disponible para todos los usuarios autenticados."""
    result = factory.list_strategies().list()
    return build_list_response(
        items=[_strategy_to_dict(s) for s in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /strategies
# ======================================================================

@router.post("", status_code=201)
def create_strategy(
    payload: CreateStrategyRequest,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Crea una nueva estrategia. Solo administradores."""
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin:
        from app.common.http import send
        return send(msg="No tienes permisos para crear estrategias.", status_code=403)

    result = factory.create_strategy().create(
        name=payload.name,
        version=payload.version,
        parameters=payload.parameters,
        description=payload.description,
    )

    if not result.success:
        return build_error_response(result, STRATEGY_ERROR_MESSAGES)

    return build_created_response(
        data=_strategy_to_dict(result.data),
        msg="Estrategia creada exitosamente.",
    )


# ======================================================================
# GET /strategies/{strategy_id}
# ======================================================================

@router.get("/{strategy_id}", status_code=200)
def get_strategy(
    strategy_id: int,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Obtiene una estrategia por ID. Disponible para todos los usuarios autenticados."""
    result = factory.get_strategy().get(strategy_id=strategy_id)

    if not result.success:
        return build_error_response(result, STRATEGY_ERROR_MESSAGES)

    return build_success_response(
        data=_strategy_to_dict(result.data),
        msg="OK",
    )


# ======================================================================
# PUT /strategies/{strategy_id}
# ======================================================================

@router.put("/{strategy_id}", status_code=200)
def update_strategy(
    strategy_id: int,
    payload: UpdateStrategyRequest,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Actualiza una estrategia existente. Solo administradores."""
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin:
        from app.common.http import send
        return send(msg="No tienes permisos para modificar estrategias.", status_code=403)

    result = factory.update_strategy().update(
        strategy_id=strategy_id,
        name=payload.name,
        version=payload.version,
        description=payload.description,
        parameters=payload.parameters,
    )

    if not result.success:
        return build_error_response(result, STRATEGY_ERROR_MESSAGES)

    return build_success_response(
        data=_strategy_to_dict(result.data),
        msg="Estrategia actualizada exitosamente.",
    )
