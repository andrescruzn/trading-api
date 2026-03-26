# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/rest/investors/routes.py
#
# ENDPOINTS:
# - GET  /api/investors           → listar inversores (admin)
# - POST /api/investors           → crear inversor (admin)
# - GET  /api/investors/{id}      → detalle (admin)
# - PUT  /api/investors/{id}      → actualizar fee_pct / is_active (admin)
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_created_response, build_error_response, build_list_response, send
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.providers.billing_provider import BillingServiceFactory, get_billing_factory

from .error_messages import INVESTOR_ERROR_MESSAGES
from .schemas import CreateInvestorRequest, UpdateInvestorRequest

router = APIRouter(prefix="/api/investors", tags=["Billing — Investors"])


def get_factory(db: Session = Depends(get_db)) -> BillingServiceFactory:
    return get_billing_factory(db)


def _investor_to_dict(inv: Investor) -> dict[str, Any]:
    return {
        "id":         inv.id,
        "user_id":    inv.user_id,
        "fee_pct":    str(inv.fee_pct),
        "is_active":  inv.is_active,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
    }


def _require_admin(identity: dict) -> bool:
    return int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)


# ======================================================================
# GET /api/investors
# ======================================================================

@router.get("", status_code=200)
def list_investors(
    only_active: bool = False,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    role_id = int(identity.get("role_id", 0))
    is_admin    = role_id == int(settings.AUTH_ADMIN_ROLE_ID)
    is_investor = role_id == int(settings.AUTH_INVESTOR_ROLE_ID)

    # Un inversor puede consultar su propio perfil (para el dashboard)
    if is_investor:
        inv = factory._investor_repo.find_by_user_id(identity.get("user_id"))
        items = [_investor_to_dict(inv)] if inv else []
        return build_list_response(items=items, msg="OK")

    if not is_admin:
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.list_investors().execute(only_active=only_active)
    return build_list_response(
        items=[_investor_to_dict(inv) for inv in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /api/investors
# ======================================================================

@router.post("", status_code=201)
def create_investor(
    payload: CreateInvestorRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.create_investor().execute(
        user_id=payload.user_id,
        fee_pct=payload.fee_pct,
    )
    if not result.success:
        return build_error_response(result, INVESTOR_ERROR_MESSAGES)

    return build_created_response(data=_investor_to_dict(result.data), msg="Inversor creado.")


# ======================================================================
# GET /api/investors/{id}
# ======================================================================

@router.get("/{investor_id}", status_code=200)
def get_investor(
    investor_id: int,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    investor = factory._investor_repo.find_by_id(investor_id)
    if not investor:
        return send(msg="Inversor no encontrado.", status_code=404, data={})

    return send(msg="OK", status_code=200, data=_investor_to_dict(investor))


# ======================================================================
# PUT /api/investors/{id}
# ======================================================================

@router.put("/{investor_id}", status_code=200)
def update_investor(
    investor_id: int,
    payload: UpdateInvestorRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.update_investor().execute(
        investor_id=investor_id,
        fee_pct=payload.fee_pct,
        is_active=payload.is_active,
    )
    if not result.success:
        return build_error_response(result, INVESTOR_ERROR_MESSAGES)

    return send(msg="Inversor actualizado.", status_code=200, data=_investor_to_dict(result.data))
