# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/deposits/routes.py
#
# ENDPOINTS (depósitos al fondo común):
# - GET  /fund/deposits/info              → cómo depositar: redes y direcciones (con sesión)
# - POST /fund/deposits                   → registrar un depósito enviado (con sesión)
# - GET  /fund/deposits                   → solicitudes (cada quien las suyas; staff, todas)
# - POST /fund/deposits/{id}/cancel       → anular la propia mientras está pendiente
# - POST /fund/deposits/{id}/confirm      → confirmar (super admin)
# - POST /fund/deposits/{id}/reject       → rechazar con motivo (super admin)
# - POST /fund/deposits/verify            → verificar ahora contra el exchange (super admin)
# - GET  /fund/deposits/unclaimed         → depósitos del exchange sin solicitud (staff)
# - POST /fund/deposits/unclaimed/assign  → asignar uno a una persona (super admin)
#
# NOTA:
# - El socio es de solo lectura, pero puede depositar dinero propio:
#   POST /fund/deposits y /cancel están en read_only_policy.py.
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
from app.common.security.jwt import (
    is_staff,
    staff_required,
    super_admin_required,
    token_required_actual,
)
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import (
    AssignUnclaimedRequest,
    ConfirmDepositRequest,
    CreateDepositRequest,
    RejectDepositRequest,
)
from app.modules.fund.rest.serializers import (
    deposit_info_to_dict,
    deposit_request_to_dict,
    exchange_deposit_to_dict,
)

router = APIRouter(prefix="/fund/deposits", tags=["Fund — Deposits"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


# ======================================================================
# Participante
# ======================================================================

@router.get("/info", status_code=200)
def get_deposit_info(
    _identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Moneda, redes con la dirección de la billetera y permanencia mínima."""
    result = factory.fund_settings().deposit_info()
    return build_success_response(data=deposit_info_to_dict(result.data))


@router.post("", status_code=201)
def create_deposit_request(
    payload: CreateDepositRequest,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Registra un depósito enviado a la billetera; se verifica solo contra el exchange."""
    result = factory.create_deposit_request().create(
        user_id=int(identity["user_id"]),
        network=payload.network,
        txid=payload.txid,
        amount=payload.amount,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=deposit_request_to_dict(result.data),
        msg="Depósito registrado. Lo confirmamos en cuanto aparezca en el exchange.",
    )


@router.get("", status_code=200)
def list_deposit_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status: str | None = Query(default=None, max_length=16),
    user_id: int | None = Query(default=None, gt=0, description="Solo staff: depósitos de esa persona."),
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Solicitudes de depósito, de la más reciente a la más antigua (paginado)."""
    owner_id = user_id if is_staff(identity) else int(identity["user_id"])
    result = factory.resolve_deposit_request().list(
        page=PageRequest.of(page, page_size), owner_id=owner_id, status=status
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    data = result.data
    return build_paginated_response(
        items=[deposit_request_to_dict(r) for r in data.items],
        total=data.total,
        page=data.page,
        page_size=data.page_size,
    )


@router.post("/{request_id}/cancel", status_code=200)
def cancel_deposit_request(
    request_id: int,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Anula la propia solicitud mientras sigue pendiente."""
    result = factory.resolve_deposit_request().cancel(request_id, int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=deposit_request_to_dict(result.data), msg="Depósito anulado.")


# ======================================================================
# Super admin
# ======================================================================

@router.post("/verify", status_code=200)
def verify_deposits(
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Revisa ahora las solicitudes pendientes contra el exchange."""
    result = factory.verify_deposits().verify()
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    s = result.data
    return build_success_response(
        data={
            "checked":   s.checked,
            "confirmed": s.confirmed,
            "review":    s.review,
            "expired":   s.expired,
            "waiting":   s.waiting,
        },
        msg="Verificación terminada.",
    )


@router.post("/{request_id}/confirm", status_code=200)
def confirm_deposit_request(
    request_id: int,
    payload: ConfirmDepositRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Confirma un depósito pendiente o en revisión y lo acredita."""
    result = factory.resolve_deposit_request().confirm(
        request_id,
        requester_user_id=int(identity["user_id"]),
        amount=payload.amount,
        note=payload.note,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(
        data=deposit_request_to_dict(result.data),
        msg="Depósito confirmado. Ya está en el saldo pendiente de asignar.",
    )


@router.post("/{request_id}/reject", status_code=200)
def reject_deposit_request(
    request_id: int,
    payload: RejectDepositRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Rechaza un depósito pendiente o en revisión, con motivo."""
    result = factory.resolve_deposit_request().reject(
        request_id, requester_user_id=int(identity["user_id"]), note=payload.note
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=deposit_request_to_dict(result.data), msg="Depósito rechazado.")


@router.get("/unclaimed", status_code=200)
def list_unclaimed_deposits(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Depósitos que entraron a la billetera sin solicitud de nadie (últimos 30 días)."""
    result = factory.unclaimed_deposits().list()
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_list_response(items=[exchange_deposit_to_dict(d) for d in result.data])


@router.post("/unclaimed/assign", status_code=201)
def assign_unclaimed_deposit(
    payload: AssignUnclaimedRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Asigna un depósito sin reclamar a una persona y lo acredita."""
    result = factory.unclaimed_deposits().assign(
        txid=payload.txid,
        user_id=payload.user_id,
        requester_user_id=int(identity["user_id"]),
        note=payload.note,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=deposit_request_to_dict(result.data),
        msg="Depósito asignado y acreditado.",
    )
