# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/model_runs/routes.py
#
# ENDPOINTS para ejecuciones de entrenamiento:
# - GET  /api/model-runs?model_id=X → listar runs de un modelo
# - POST /api/model-runs             → iniciar run (admin)
# - POST /api/model-runs/{id}/finish → finalizar run (admin)
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
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.agent.domain.model_run_entity import ModelRun
from app.modules.agent.providers import AgentServiceFactory

from .error_messages import MODEL_RUN_ERROR_MESSAGES
from .schemas import CreateModelRunRequest, FinishModelRunRequest

router = APIRouter(prefix="/api/model-runs", tags=["Model Runs"])


def get_factory(db: Session = Depends(get_db)) -> AgentServiceFactory:
    return AgentServiceFactory(session=db)


def _run_to_dict(r: ModelRun) -> dict[str, Any]:
    return {
        "id":          r.id,
        "model_id":    r.model_id,
        "dataset_id":  r.dataset_id,
        "status":      r.status,
        "metrics":     r.metrics,
        "params":      r.params,
        "logs_uri":    r.logs_uri,
        "started_at":  r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }


@router.get("", status_code=200)
def list_model_runs(
    model_id: int = Query(..., ge=1),
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    result = factory.list_model_runs().list(model_id=model_id)
    return build_list_response(
        items=[_run_to_dict(r) for r in (result.data or [])],
        msg="OK",
    )


@router.post("", status_code=201)
def create_model_run(
    payload: CreateModelRunRequest,
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No tienes permisos para iniciar entrenamientos.", status_code=403)

    result = factory.create_model_run().create(
        model_id=payload.model_id,
        params=payload.params,
        dataset_id=payload.dataset_id,
        logs_uri=payload.logs_uri,
    )
    if not result.success:
        return build_error_response(result, MODEL_RUN_ERROR_MESSAGES)
    return build_created_response(data=_run_to_dict(result.data), msg="Entrenamiento iniciado.")


@router.post("/{run_id}/finish", status_code=200)
def finish_model_run(
    run_id: int,
    payload: FinishModelRunRequest,
    identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No tienes permisos para finalizar entrenamientos.", status_code=403)

    result = factory.finish_model_run().finish(
        run_id=run_id,
        status=payload.status,
        metrics=payload.metrics,
        logs_uri=payload.logs_uri,
    )
    if not result.success:
        return build_error_response(result, MODEL_RUN_ERROR_MESSAGES)
    return build_success_response(data=_run_to_dict(result.data), msg="Entrenamiento finalizado.")
