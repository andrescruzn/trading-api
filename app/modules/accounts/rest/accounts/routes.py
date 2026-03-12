# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/accounts/routes.py
#
# ENDPOINTS:
# - GET  /accounts              → listar cuentas del usuario (admin: todas)
# - POST /accounts              → crear cuenta
# - GET  /accounts/{id}         → obtener cuenta por ID
# - PUT  /accounts/{id}         → actualizar cuenta
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_list_response,
    build_created_response,
    build_success_response,
)
from app.common.config import settings
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.providers import AccountServiceFactory

from .error_messages import ACCOUNT_ERROR_MESSAGES
from .schemas import CreateAccountRequest, UpdateAccountRequest

router = APIRouter(prefix="/accounts", tags=["Accounts"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> AccountServiceFactory:
    return AccountServiceFactory(session=db)


# ======================================================================
# Helper: serializar Account a dict (nunca exponer enc_creds)
# ======================================================================

def _account_to_dict(account: Account) -> dict[str, Any]:
    # Filtrar credenciales cifradas del meta antes de exponer
    safe_meta = {k: v for k, v in account.meta.items() if k != "enc_creds"}
    return {
        "id":              account.id,
        "user_id":         account.user_id,
        "exchange_id":     account.exchange_id,
        "name":            account.name,
        "mode":            account.mode,
        "base_currency":   account.base_currency,
        "status":          account.status,
        "credentials_ref": account.credentials_ref,
        "has_credentials": "enc_creds" in account.meta,
        "meta":            safe_meta,
        "created_at":      account.created_at.isoformat() if account.created_at else None,
        "updated_at":      account.updated_at.isoformat() if account.updated_at else None,
    }


# ======================================================================
# GET /accounts
# ======================================================================

@router.get("", status_code=200)
def list_accounts(
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Lista las cuentas. Admin ve todas; usuario normal ve las suyas."""
    user_id = int(identity["user_id"])
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    result = factory.list_accounts().list(user_id=user_id, is_admin=is_admin)

    return build_list_response(
        items=[_account_to_dict(a) for a in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /accounts
# ======================================================================

@router.post("", status_code=201)
def create_account(
    payload: CreateAccountRequest,
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Crea una nueva cuenta de trading para el usuario autenticado."""
    user_id = int(identity["user_id"])

    result = factory.create_account().create(
        user_id=user_id,
        name=payload.name,
        mode=payload.mode,
        base_currency=payload.base_currency,
        exchange_id=payload.exchange_id,
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        credentials_label=payload.credentials_label,
    )

    if not result.success:
        return build_error_response(result, ACCOUNT_ERROR_MESSAGES)

    return build_created_response(
        data=_account_to_dict(result.data),
        msg="Cuenta creada exitosamente.",
    )


# ======================================================================
# GET /accounts/{account_id}
# ======================================================================

@router.get("/{account_id}", status_code=200)
def get_account(
    account_id: int,
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Obtiene una cuenta por ID. Solo el dueño o un admin."""
    user_id = int(identity["user_id"])
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    result = factory.get_account().get(
        account_id=account_id,
        requester_user_id=user_id,
        is_admin=is_admin,
    )

    if not result.success:
        return build_error_response(result, ACCOUNT_ERROR_MESSAGES)

    return build_success_response(
        data=_account_to_dict(result.data),
        msg="OK",
    )


# ======================================================================
# PUT /accounts/{account_id}
# ======================================================================

@router.put("/{account_id}", status_code=200)
def update_account(
    account_id: int,
    payload: UpdateAccountRequest,
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Actualiza una cuenta. Solo el dueño o un admin."""
    user_id = int(identity["user_id"])
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    result = factory.update_account().update(
        account_id=account_id,
        requester_user_id=user_id,
        is_admin=is_admin,
        name=payload.name,
        status=payload.status,
        exchange_id=payload.exchange_id,
        base_currency=payload.base_currency,
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        credentials_label=payload.credentials_label,
    )

    if not result.success:
        return build_error_response(result, ACCOUNT_ERROR_MESSAGES)

    return build_success_response(
        data=_account_to_dict(result.data),
        msg="Cuenta actualizada exitosamente.",
    )
