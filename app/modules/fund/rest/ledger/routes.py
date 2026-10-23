# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/ledger/routes.py
#
# ENDPOINTS (libro mayor del fondo común):
# - GET  /fund/me/balances                      → mis saldos (con sesión)
# - GET  /fund/me/ledger                        → mis movimientos, paginados (con sesión)
# - GET  /fund/participants                     → saldos de cada persona (staff)
# - GET  /fund/participants/{user_id}/ledger    → movimientos de una persona (staff)
# - POST /fund/participants/{user_id}/refunds   → devolución excepcional (super admin)
#
# SEGURIDAD:
# - Un inversor solo ve lo suyo (/me). Nada de esto expone el saldo total
#   de la billetera.
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.contracts import PageRequest
from app.common.contracts.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_paginated_response,
    build_success_response,
)
from app.common.security.jwt import staff_required, super_admin_required, token_required_actual
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import RefundRequest
from app.modules.fund.rest.serializers import balances_to_dict, ledger_entry_to_dict

router = APIRouter(prefix="/fund", tags=["Fund — Ledger"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


def _ledger_page(factory: FundServiceFactory, user_id: int, page: int, page_size: int):
    data = factory.ledger().ledger(user_id, PageRequest.of(page, page_size)).data
    return build_paginated_response(
        items=[ledger_entry_to_dict(e) for e in data.items],
        total=data.total,
        page=data.page,
        page_size=data.page_size,
    )


@router.get("/me/balances", status_code=200)
def get_my_balances(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Mis saldos en el fondo: pendiente de asignar y disponible."""
    result = factory.ledger().balances(int(identity["user_id"]))
    return build_success_response(data=balances_to_dict(result.data))


@router.get("/me/ledger", status_code=200)
def get_my_ledger(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Mis movimientos, del más reciente al más antiguo."""
    return _ledger_page(factory, int(identity["user_id"]), page, page_size)


@router.get("/participants", status_code=200)
def list_participant_balances(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Saldos de cada persona con movimientos en el fondo (super admin y socio)."""
    result = factory.ledger().all_balances()
    return build_list_response(items=[balances_to_dict(b) for b in result.data])


@router.get("/participants/{user_id}/ledger", status_code=200)
def get_participant_ledger(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Movimientos de una persona (super admin y socio)."""
    return _ledger_page(factory, user_id, page, page_size)


@router.post("/participants/{user_id}/refunds", status_code=201)
def refund_pending_balance(
    user_id: int,
    payload: RefundRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Devolución excepcional de saldo pendiente de asignar, con motivo (super admin)."""
    result = factory.ledger().refund(
        user_id=user_id,
        amount=payload.amount,
        reason=payload.reason,
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=ledger_entry_to_dict(result.data),
        msg="Devolución registrada. Recuerda enviar el dinero desde el exchange.",
    )
