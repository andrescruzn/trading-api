# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/datasets/routes.py
#
# ENDPOINTS:
# - GET  /datasets         → listar todos (cualquier usuario)
# - POST /datasets         → crear (admin)
# - GET  /datasets/{id}    → obtener por ID (cualquier usuario)
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
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.providers import StrategyServiceFactory

from .error_messages import DATASET_ERROR_MESSAGES
from .schemas import CreateDatasetRequest

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> StrategyServiceFactory:
    return StrategyServiceFactory(session=db)


# ======================================================================
# Serializer
# ======================================================================

def _dataset_to_dict(d: Dataset) -> dict[str, Any]:
    return {
        "id":           d.id,
        "name":         d.name,
        "description":  d.description,
        "symbol_id":    d.symbol_id,
        "timeframe_id": d.timeframe_id,
        "start_ts":     d.start_ts.isoformat() if d.start_ts else None,
        "end_ts":       d.end_ts.isoformat() if d.end_ts else None,
        "dataset_hash": d.dataset_hash,
        "query_spec":   d.query_spec,
        "created_at":   d.created_at.isoformat() if d.created_at else None,
    }


# ======================================================================
# GET /datasets
# ======================================================================

@router.get("", status_code=200)
def list_datasets(
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Lista todos los datasets. Disponible para todos los usuarios autenticados."""
    result = factory.list_datasets().list()
    return build_list_response(
        items=[_dataset_to_dict(d) for d in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /datasets
# ======================================================================

@router.post("", status_code=201)
def create_dataset(
    payload: CreateDatasetRequest,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Crea un nuevo dataset de backtesting. Solo administradores."""
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin:
        return send(msg="No tienes permisos para crear datasets.", status_code=403)

    result = factory.create_dataset().create(
        name=payload.name,
        query_spec=payload.query_spec,
        description=payload.description,
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        start_ts=payload.start_ts,
        end_ts=payload.end_ts,
    )

    if not result.success:
        return build_error_response(result, DATASET_ERROR_MESSAGES)

    return build_created_response(
        data=_dataset_to_dict(result.data),
        msg="Dataset creado exitosamente.",
    )


# ======================================================================
# GET /datasets/{dataset_id}
# ======================================================================

@router.get("/{dataset_id}", status_code=200)
def get_dataset(
    dataset_id: int,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Obtiene un dataset por ID."""
    result = factory.get_dataset().get(dataset_id=dataset_id)

    if not result.success:
        return build_error_response(result, DATASET_ERROR_MESSAGES)

    return build_success_response(
        data=_dataset_to_dict(result.data),
        msg="OK",
    )
