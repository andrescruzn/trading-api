# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/rest/feature_sets/routes.py
#
# ENDPOINTS:
# - GET  /feature-sets       → lista todos (autenticado)
# - POST /feature-sets       → crea nuevo (solo admin)
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_created_response
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.features.providers import FeatureServiceFactory

from .error_messages import FEATURE_SET_ERROR_MESSAGES
from .schemas import CreateFeatureSetRequest

router = APIRouter(prefix="/feature-sets", tags=["Features — Feature Sets"])


def get_factory(db: Session = Depends(get_db)) -> FeatureServiceFactory:
    return FeatureServiceFactory(session=db)


def _fs_to_dict(fs: Any) -> dict:
    return {
        "id": fs.id,
        "name": fs.name,
        "version": fs.version,
        "description": fs.description,
        "spec": fs.spec,
        "created_at": fs.created_at.isoformat() if fs.created_at else None,
    }


# ======================================================================
# GET /feature-sets
# ======================================================================

@router.get("", status_code=200)
def list_feature_sets(
    _identity: dict = Depends(token_required_actual),
    factory: FeatureServiceFactory = Depends(get_factory),
):
    """Lista todos los feature sets disponibles."""
    result = factory.list_feature_sets().list()
    return build_list_response(
        items=[_fs_to_dict(fs) for fs in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /feature-sets
# ======================================================================

@router.post("", status_code=201)
def create_feature_set(
    payload: CreateFeatureSetRequest,
    _identity: dict = Depends(admin_required),
    factory: FeatureServiceFactory = Depends(get_factory),
):
    """Crea un nuevo feature set. Solo admins."""
    result = factory.create_feature_set().create(
        name=payload.name,
        version=payload.version,
        spec=payload.spec,
        description=payload.description,
    )
    if not result.success:
        return build_error_response(result, FEATURE_SET_ERROR_MESSAGES)

    return build_created_response(data=_fs_to_dict(result.data), msg="Feature set creado.")
