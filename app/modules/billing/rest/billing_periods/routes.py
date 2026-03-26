# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/rest/billing_periods/routes.py
#
# ENDPOINTS:
# - GET  /api/billing-periods              → listar períodos de una cuenta
# - POST /api/billing-periods/open         → abrir período (admin)
# - POST /api/billing-periods/{id}/close   → cerrar período con HWM (admin)
# - GET  /api/fee-transactions             → listar transacciones de fee
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_created_response, build_error_response, build_list_response, send
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.providers.billing_provider import BillingServiceFactory, get_billing_factory

from .error_messages import BILLING_PERIOD_ERROR_MESSAGES
from .schemas import CloseBillingPeriodRequest, OpenBillingPeriodRequest

router = APIRouter(tags=["Billing — Periods & Fees"])


def get_factory(db: Session = Depends(get_db)) -> BillingServiceFactory:
    return get_billing_factory(db)


def _period_to_dict(p: BillingPeriod) -> dict[str, Any]:
    return {
        "id":                   p.id,
        "managed_account_id":   p.managed_account_id,
        "start_ts":             p.start_ts.isoformat() if p.start_ts else None,
        "end_ts":               p.end_ts.isoformat() if p.end_ts else None,
        "opening_equity":       str(p.opening_equity),
        "closing_equity":       str(p.closing_equity) if p.closing_equity is not None else None,
        "gross_pnl":            str(p.gross_pnl) if p.gross_pnl is not None else None,
        "fee_pct":              str(p.fee_pct),
        "fee_amount":           str(p.fee_amount) if p.fee_amount is not None else None,
        "net_pnl":              str(p.net_pnl) if p.net_pnl is not None else None,
        "status":               p.status,
        "created_at":           p.created_at.isoformat() if p.created_at else None,
        "closed_at":            p.closed_at.isoformat() if p.closed_at else None,
    }


def _fee_tx_to_dict(tx: FeeTransaction) -> dict[str, Any]:
    return {
        "id":                   tx.id,
        "billing_period_id":    tx.billing_period_id,
        "managed_account_id":   tx.managed_account_id,
        "amount":               str(tx.amount),
        "status":               tx.status,
        "charged_at":           tx.charged_at.isoformat() if tx.charged_at else None,
        "notes":                tx.notes,
        "created_at":           tx.created_at.isoformat() if tx.created_at else None,
    }


def _require_admin(identity: dict) -> bool:
    return int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)


def _is_investor(identity: dict) -> bool:
    return int(identity.get("role_id", 0)) == int(settings.AUTH_INVESTOR_ROLE_ID)


# ======================================================================
# GET /api/billing-periods?managed_account_id=X
# ======================================================================

@router.get("/api/billing-periods", status_code=200)
def list_billing_periods(
    managed_account_id: int,
    limit: int = 50,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    investor_id: int | None = None
    if _is_investor(identity):
        inv = factory._investor_repo.find_by_user_id(identity.get("user_id"))
        if not inv:
            return build_list_response(items=[], msg="OK")
        investor_id = inv.id
    elif not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.list_billing_periods().execute(
        managed_account_id=managed_account_id,
        investor_id=investor_id,
        limit=limit,
    )
    if not result.success:
        return build_error_response(result, BILLING_PERIOD_ERROR_MESSAGES)

    return build_list_response(
        items=[_period_to_dict(p) for p in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /api/billing-periods/open
# ======================================================================

@router.post("/api/billing-periods/open", status_code=201)
def open_billing_period(
    payload: OpenBillingPeriodRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.open_billing_period().execute(
        managed_account_id=payload.managed_account_id,
        opening_equity=payload.opening_equity,
    )
    if not result.success:
        return build_error_response(result, BILLING_PERIOD_ERROR_MESSAGES)

    return build_created_response(data=_period_to_dict(result.data), msg="Período abierto.")


# ======================================================================
# POST /api/billing-periods/{id}/close
# ======================================================================

@router.post("/api/billing-periods/{period_id}/close", status_code=200)
def close_billing_period(
    period_id: int,
    payload: CloseBillingPeriodRequest,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    if not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.close_billing_period().execute(
        period_id=period_id,
        closing_equity=payload.closing_equity,
    )
    if not result.success:
        return build_error_response(result, BILLING_PERIOD_ERROR_MESSAGES)

    return send(msg="Período cerrado.", status_code=200, data=_period_to_dict(result.data))


# ======================================================================
# GET /api/fee-transactions?managed_account_id=X
# ======================================================================

@router.get("/api/fee-transactions", status_code=200)
def list_fee_transactions(
    managed_account_id: int,
    limit: int = 50,
    identity: dict = Depends(token_required_actual),
    factory: BillingServiceFactory = Depends(get_factory),
):
    investor_id: int | None = None
    if _is_investor(identity):
        inv = factory._investor_repo.find_by_user_id(identity.get("user_id"))
        if not inv:
            return build_list_response(items=[], msg="OK")
        investor_id = inv.id
    elif not _require_admin(identity):
        return send(msg="No autorizado.", status_code=403, data={})

    result = factory.list_fee_transactions().execute(
        managed_account_id=managed_account_id,
        investor_id=investor_id,
        limit=limit,
    )
    if not result.success:
        return build_error_response(result, BILLING_PERIOD_ERROR_MESSAGES)

    return build_list_response(
        items=[_fee_tx_to_dict(tx) for tx in (result.data or [])],
        msg="OK",
    )
