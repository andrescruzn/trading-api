# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/payouts/routes.py
#
# ENDPOINTS (retiros del fondo común, F5; entre billeteras desde 2026-10-26):
# - GET  /fund/withdrawals/networks                 → redes de retiro (comisión y mínimo)
# - GET  /fund/me/payout-methods                    → mis direcciones de retiro (enmascaradas)
# - POST /fund/me/payout-methods                    → registrar una (red, dirección, memo)
# - POST /fund/me/payout-methods/{id}/deactivate    → dejar de usarlo
# - GET  /fund/me/withdrawable                      → lo que puedo retirar hoy
# - POST /fund/withdrawals                          → pedir un retiro
# - GET  /fund/withdrawals                          → retiros (los míos; staff, todos)
# - POST /fund/withdrawals/{id}/cancel              → anular el mío sin pagar
# - GET  /fund/withdrawals/{id}/payout-details      → dirección completa para enviar (super admin)
# - POST /fund/withdrawals/{id}/lookup              → buscar el txid en Binance (super admin)
# - POST /fund/withdrawals/{id}/pay                 → registrar el envío (super admin)
# - POST /fund/withdrawals/{id}/reject              → rechazarlo con motivo (super admin)
#
# SEGURIDAD:
# - La dirección completa solo sale para un super admin y solo de un
#   retiro concreto; en todo lo demás, el resumen enmascarado.
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
from app.common.security.jwt import is_staff, super_admin_required, token_required_actual
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import (
    PayoutMethodCreateRequest,
    ReceiptFileRequest,
    WithdrawalCreateRequest,
    WithdrawalLookupRequest,
    WithdrawalPayRequest,
    WithdrawalRejectRequest,
)
from app.modules.fund.rest.serializers import (
    payout_method_to_dict,
    receipt_to_dict,
    withdraw_networks_to_dict,
    withdrawal_check_to_dict,
    withdrawal_to_dict,
)

router = APIRouter(prefix="/fund", tags=["Fund — Withdrawals"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


# ======================================================================
# Medios de pago (direcciones cripto)
# ======================================================================

@router.get("/withdrawals/networks", status_code=200)
def list_withdraw_networks(
    _identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Redes por las que el fondo envía los retiros, con la comisión de Binance."""
    result = factory.payout_methods().networks()
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=withdraw_networks_to_dict(result.data))


@router.get("/me/payout-methods", status_code=200)
def list_my_payout_methods(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Mis medios de pago activos (sin los datos completos)."""
    result = factory.payout_methods().list_mine(int(identity["user_id"]))
    return build_list_response(items=[payout_method_to_dict(m) for m in result.data])


@router.post("/me/payout-methods", status_code=201)
def create_payout_method(
    payload: PayoutMethodCreateRequest,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Registra una dirección de retiro; se puede usar tras la espera de seguridad."""
    details = payload.model_dump(exclude={"kind", "label"}, exclude_none=True)
    result = factory.payout_methods().create(
        user_id=int(identity["user_id"]), kind=payload.kind, label=payload.label, details=details
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=payout_method_to_dict(result.data),
        msg="Dirección guardada. Por seguridad podrás usarla dentro de 48 horas.",
    )


@router.post("/me/payout-methods/{method_id}/deactivate", status_code=200)
def deactivate_payout_method(
    method_id: int,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Desactiva una de mis direcciones de retiro."""
    result = factory.payout_methods().deactivate(int(identity["user_id"]), method_id)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=None, msg="Dirección desactivada.")


# ======================================================================
# Retiros
# ======================================================================

@router.get("/me/withdrawable", status_code=200)
def get_my_withdrawable(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Lo que puedo retirar hoy (disponible − retiros sin pagar − reinversión en cola)."""
    free = factory.withdrawals().free_available(int(identity["user_id"]))
    return build_success_response(data={"withdrawable": str(max(free, 0))})


@router.post("/withdrawals", status_code=201)
def create_withdrawal(
    payload: WithdrawalCreateRequest,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Pide un retiro de mi saldo disponible a una de mis direcciones."""
    result = factory.withdrawals().create(
        user_id=int(identity["user_id"]),
        amount=payload.amount,
        payout_method_id=payload.payout_method_id,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=withdrawal_to_dict(result.data),
        msg="Retiro pedido. Te avisaremos cuando enviemos el dinero a tu dirección.",
    )


@router.get("/withdrawals", status_code=200)
def list_withdrawals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status: str | None = Query(default=None, max_length=16),
    user_id: int | None = Query(default=None, gt=0, description="Solo staff: retiros de esa persona."),
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Retiros, del más reciente al más antiguo (paginado)."""
    owner_id = user_id if is_staff(identity) else int(identity["user_id"])
    result = factory.withdrawals().list(
        page=PageRequest.of(page, page_size), owner_id=owner_id, status=status
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    data = result.data
    return build_paginated_response(
        items=[withdrawal_to_dict(w) for w in data.items],
        total=data.total,
        page=data.page,
        page_size=data.page_size,
    )


@router.post("/withdrawals/{request_id}/cancel", status_code=200)
def cancel_withdrawal(
    request_id: int,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Anula mi retiro mientras no se haya pagado."""
    result = factory.withdrawals().cancel(request_id, int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=withdrawal_to_dict(result.data), msg="Retiro anulado.")


@router.get("/withdrawals/{request_id}/payout-details", status_code=200)
def get_payout_details(
    request_id: int,
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Dirección completa (red, dirección y memo) de un retiro, para enviarlo (super admin)."""
    withdrawal = factory.withdrawals().get(request_id)
    if not withdrawal.success:
        return build_error_response(withdrawal, FUND_ERROR_MESSAGES)
    result = factory.payout_methods().details_for_payment(withdrawal.data.payout_method_id)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=payout_method_to_dict(result.data, with_details=True))


@router.post("/withdrawals/{request_id}/lookup", status_code=200)
def lookup_withdrawal(
    request_id: int,
    payload: WithdrawalLookupRequest,
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Busca el txid en los retiros de Binance y lo compara con el pedido (no cambia nada)."""
    result = factory.withdrawals().lookup(request_id, payload.txid)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=withdrawal_check_to_dict(result.data))


@router.post("/withdrawals/{request_id}/pay", status_code=200)
def pay_withdrawal(
    request_id: int,
    payload: WithdrawalPayRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Registra el envío del retiro (txid); con billetera live se comprueba en Binance."""
    result = factory.withdrawals().mark_paid(
        request_id,
        requester_user_id=int(identity["user_id"]),
        txid=payload.txid,
        sent_amount=payload.sent_amount,
        network_fee=payload.network_fee,
        note=payload.note,
        receipt_filename=payload.receipt.filename if payload.receipt else None,
        receipt_base64=payload.receipt.data_base64 if payload.receipt else None,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(
        data=withdrawal_to_dict(result.data),
        msg="Envío registrado. Le avisamos a la persona con los detalles.",
    )


@router.put("/withdrawals/{request_id}/receipt", status_code=200)
def attach_withdrawal_receipt(
    request_id: int,
    payload: ReceiptFileRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Sube o cambia el comprobante de un retiro pagado (PDF, PNG o JPG, máx. 5 MB)."""
    result = factory.withdrawals().attach_receipt(
        request_id,
        requester_user_id=int(identity["user_id"]),
        filename=payload.filename,
        data_base64=payload.data_base64,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=withdrawal_to_dict(result.data), msg="Comprobante guardado.")


@router.get("/withdrawals/{request_id}/receipt", status_code=200)
def get_withdrawal_receipt(
    request_id: int,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """El comprobante en base64: la persona del retiro o el staff."""
    result = factory.withdrawals().get_receipt(
        request_id, user_id=int(identity["user_id"]), is_staff=is_staff(identity)
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=receipt_to_dict(result.data))


@router.post("/withdrawals/{request_id}/reject", status_code=200)
def reject_withdrawal(
    request_id: int,
    payload: WithdrawalRejectRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Rechaza un retiro sin pagar, con motivo."""
    result = factory.withdrawals().reject(
        request_id, requester_user_id=int(identity["user_id"]), note=payload.note
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=withdrawal_to_dict(result.data), msg="Retiro rechazado.")
