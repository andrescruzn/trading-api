# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/balances/routes.py
#
# ENDPOINTS:
# - GET  /accounts/{id}/balances  → listar balances de la cuenta
# - POST /accounts/{id}/balances  → registrar snapshot de balance
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_list_response,
    build_created_response,
)
from app.common.config import settings
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.providers import AccountServiceFactory

from .error_messages import BALANCE_ERROR_MESSAGES
from .schemas import RecordBalanceRequest

router = APIRouter(prefix="/accounts", tags=["Accounts — Balances"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> AccountServiceFactory:
    return AccountServiceFactory(session=db)


# ======================================================================
# Helper: serializar AccountBalance a dict
# ======================================================================

def _balance_to_dict(b: AccountBalance) -> dict[str, Any]:
    return {
        "id":         b.id,
        "account_id": b.account_id,
        "asset":      b.asset,
        "free":       str(b.free),
        "locked":     str(b.locked),
        "total":      str(b.total),
        "ts":         b.ts.isoformat() if b.ts else None,
    }


# ======================================================================
# GET /accounts/{account_id}/balances
# ======================================================================

@router.get("/{account_id}/balances", status_code=200)
def list_balances(
    account_id: int,
    asset: Optional[str] = Query(default=None, description="Filtrar por activo (USDT, BTC...)"),
    limit: int = Query(default=100, ge=1, le=500, description="Máximo de registros"),
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Lista los balances (snapshots) de una cuenta, ordenados del más reciente al más antiguo."""
    user_id = int(identity["user_id"])
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    result = factory.list_balances().list(
        account_id=account_id,
        requester_user_id=user_id,
        is_admin=is_admin,
        asset=asset,
        limit=limit,
    )

    if not result.success:
        return build_error_response(result, BALANCE_ERROR_MESSAGES)

    return build_list_response(
        items=[_balance_to_dict(b) for b in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /accounts/{account_id}/balances
# ======================================================================

@router.post("/{account_id}/balances", status_code=201)
def record_balance(
    account_id: int,
    payload: RecordBalanceRequest,
    identity: dict = Depends(token_required_actual),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Registra un snapshot de balance para un activo. Construye la curva de equity."""
    user_id = int(identity["user_id"])
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    result = factory.record_balance().record(
        account_id=account_id,
        requester_user_id=user_id,
        asset=payload.asset,
        free=payload.free,
        locked=payload.locked,
        is_admin=is_admin,
    )

    if not result.success:
        return build_error_response(result, BALANCE_ERROR_MESSAGES)

    return build_created_response(
        data=_balance_to_dict(result.data),
        msg="Balance registrado exitosamente.",
    )
