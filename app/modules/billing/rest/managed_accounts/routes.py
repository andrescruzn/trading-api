# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/rest/managed_accounts/routes.py
#
# ENDPOINTS:
# - GET  /api/managed-accounts           → listar (admin: todas; investor: las suyas)
# - POST /api/managed-accounts           → crear (admin)
# - GET  /api/managed-accounts/{id}      → detalle (admin o investor dueño)
# - PUT  /api/managed-accounts/{id}      → actualizar (admin)
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_created_response, build_error_response, build_list_response, send
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.providers.billing_provider import BillingServiceFactory, get_billing_factory

from .error_messages import MANAGED_ACCOUNT_ERROR_MESSAGES
from .schemas import CreateManagedAccountRequest, UpdateManagedAccountRequest

router = APIRouter(prefix="/api/managed-accounts", tags=["Billing — Managed Accounts"])


def get_factory(db: Session = Depends(get_db)) -> BillingServiceFactory:
    return get_billing_factory(db)


def _account_to_dict(a: ManagedAccount) -> dict[str, Any]:
    return {
        "id":               a.id,
        "investor_id":      a.investor_id,
        "account_id":       a.account_id,
        "bot_id":           a.bot_id,
        "name":             a.name,
        "initial_capital":  str(a.initial_capital),
        "high_water_mark":  str(a.high_water_mark),
        "period_type":      a.period_type,
        "is_active":        a.is_active,
        "created_at":       a.created_at.isoformat() if a.created_at else None,
        "updated_at":       a.updated_at.isoformat() if a.updated_at else None,
    }


# ======================================================================
# GET /api/managed-accounts
# ======================================================================

@router.get("", status_code=200)
def list_managed_accounts(
    only_active: bool = False,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    role_id = int(identity.get("role_id", 0))
    is_admin = role_id == int(settings.AUTH_ADMIN_ROLE_ID)
    is_investor = role_id == int(settings.AUTH_INVESTOR_ROLE_ID)

    investor_id: int | None = None
    if is_investor:
        # El inversor solo ve sus propias cuentas
        inv = factory._investor_repo.find_by_user_id(identity.get("user_id"))
        if not inv:
            return build_list_response(items=[], msg="OK")
        investor_id = inv.id
    elif not is_admin:
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.list_managed_accounts().execute(
        investor_id=investor_id,
        only_active=only_active,
    )
    return build_list_response(
        items=[_account_to_dict(a) for a in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /api/managed-accounts
# ======================================================================

@router.post("", status_code=201)
def create_managed_account(
    payload: CreateManagedAccountRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.create_managed_account().execute(
        investor_id=payload.investor_id,
        account_id=payload.account_id,
        name=payload.name,
        initial_capital=payload.initial_capital,
        period_type=payload.period_type,
        bot_id=payload.bot_id,
    )
    if not result.success:
        return build_error_response(result, MANAGED_ACCOUNT_ERROR_MESSAGES)

    return build_created_response(
        data=_account_to_dict(result.data),
        msg="Cuenta gestionada creada.",
    )


# ======================================================================
# GET /api/managed-accounts/{id}
# ======================================================================

@router.get("/{managed_account_id}", status_code=200)
def get_managed_account(
    managed_account_id: int,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    role_id = int(identity.get("role_id", 0))
    is_admin = role_id == int(settings.AUTH_ADMIN_ROLE_ID)
    is_investor = role_id == int(settings.AUTH_INVESTOR_ROLE_ID)

    investor_id: int | None = None
    if is_investor:
        inv = factory._investor_repo.find_by_user_id(identity.get("user_id"))
        if not inv:
            return send(msg="No autorizado.", status_code=403, data={})
        investor_id = inv.id

    result = factory.get_managed_account().execute(
        managed_account_id=managed_account_id,
        investor_id=investor_id if not is_admin else None,
    )
    if not result.success:
        return build_error_response(result, MANAGED_ACCOUNT_ERROR_MESSAGES)

    return send(msg="OK", status_code=200, data=_account_to_dict(result.data))


# ======================================================================
# PUT /api/managed-accounts/{id}
# ======================================================================

@router.put("/{managed_account_id}", status_code=200)
def update_managed_account(
    managed_account_id: int,
    payload: UpdateManagedAccountRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.update_managed_account().execute(
        managed_account_id=managed_account_id,
        name=payload.name,
        bot_id=payload.bot_id,
        period_type=payload.period_type,
        is_active=payload.is_active,
    )
    if not result.success:
        return build_error_response(result, MANAGED_ACCOUNT_ERROR_MESSAGES)

    return send(msg="Cuenta gestionada actualizada.", status_code=200, data=_account_to_dict(result.data))
