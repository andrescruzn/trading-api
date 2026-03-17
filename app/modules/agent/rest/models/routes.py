# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/models/routes.py
#
# ENDPOINTS para modelos ML:
# - GET  /api/models           → listar modelos (filtro: status)
# - POST /api/models           → crear modelo (admin)
# - GET  /api/models/{id}      → obtener por ID
# - PUT  /api/models/{id}      → actualizar (admin)
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.providers import AgentServiceFactory

from .error_messages import MODEL_ERROR_MESSAGES
from .schemas import CreateModelRequest, UpdateModelRequest

router = APIRouter(prefix="/api/models", tags=["ML Models"])


def get_factory(db: Session = Depends(get_db)) -> AgentServiceFactory:
    return AgentServiceFactory(session=db)


def _model_to_dict(m: MLModel) -> dict[str, Any]:
    return {
        "id":             m.id,
        "name":           m.name,
        "version":        m.version,
        "model_type":     m.model_type,
        "feature_set_id": m.feature_set_id,
        "artifact_uri":   m.artifact_uri,
        "status":         m.status,
        "meta":           m.meta,
        "created_at":     m.created_at.isoformat() if m.created_at else None,
    }


@router.get("", status_code=200)
def list_models(
    status: Optional[str] = Query(default=None),
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    result = factory.list_models().list(status=status)
    return build_list_response(
        items=[_model_to_dict(m) for m in (result.data or [])],
        msg="OK",
    )


@router.post("", status_code=201)
def create_model(
    payload: CreateModelRequest,
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No tienes permisos para crear modelos.", status_code=403)

    result = factory.create_model().create(
        name=payload.name,
        version=payload.version,
        model_type=payload.model_type,
        meta=payload.meta,
        feature_set_id=payload.feature_set_id,
        artifact_uri=payload.artifact_uri,
    )
    if not result.success:
        return build_error_response(result, MODEL_ERROR_MESSAGES)
    return build_created_response(data=_model_to_dict(result.data), msg="Modelo registrado.")


@router.get("/{model_id}", status_code=200)
def get_model(
    model_id: int,
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    result = factory.get_model().get(model_id=model_id)
    if not result.success:
        return build_error_response(result, MODEL_ERROR_MESSAGES)
    return build_success_response(data=_model_to_dict(result.data), msg="OK")


@router.put("/{model_id}", status_code=200)
def update_model(
    model_id: int,
    payload: UpdateModelRequest,
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No tienes permisos para modificar modelos.", status_code=403)

    result = factory.update_model().update(
        model_id=model_id,
        status=payload.status,
        artifact_uri=payload.artifact_uri,
        meta=payload.meta,
    )
    if not result.success:
        return build_error_response(result, MODEL_ERROR_MESSAGES)
    return build_success_response(data=_model_to_dict(result.data), msg="Modelo actualizado.")
