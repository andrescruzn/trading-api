# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/fees/routes.py
#
# ENDPOINTS (comisión del fondo común, F5):
# - GET  /fund/fees                    → tabla de tramos vigente (con sesión: transparencia)
# - GET  /fund/fees/history            → versiones anteriores (staff)
# - POST /fund/fees                    → publicar una tabla nueva (super admin)
# - GET  /fund/commission-shares       → reparto vigente y anteriores (staff)
# - PUT  /fund/commission-shares       → publicar un reparto nuevo (super admin)
# - GET  /fund/commissions             → comisión acumulada de cada propietario (staff)
# - GET  /fund/me/commissions          → las comisiones que recibí (con sesión)
#
# Los porcentajes viajan en % (20 = 20 %); el dominio los guarda en fracción.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
)
from app.common.security.jwt import staff_required, super_admin_required, token_required_actual
from app.extensions.db import get_db
from app.modules.fund.domain.commission import CommissionShare, FeeTier
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import CreateFeeScheduleRequest, SetCommissionSharesRequest
from app.modules.fund.rest.serializers import (
    commission_credit_to_dict,
    commission_shares_to_dict,
    fee_schedule_to_dict,
    owner_earning_to_dict,
)

router = APIRouter(prefix="/fund", tags=["Fund — Fees"])

_HUNDRED = Decimal("100")


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


# ======================================================================
# Tabla de tramos
# ======================================================================

@router.get("/fees", status_code=200)
def get_fee_schedule(
    _identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Tabla de tramos vigente (`null` si aún no se configuró)."""
    current = factory.fee_schedule().current().data
    return build_success_response(data=fee_schedule_to_dict(current) if current else None)


@router.get("/fees/history", status_code=200)
def list_fee_schedules(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Versiones de la tabla de tramos, de la más nueva a la más vieja."""
    result = factory.fee_schedule().history()
    return build_list_response(items=[fee_schedule_to_dict(f) for f in result.data])


@router.post("/fees", status_code=201)
def create_fee_schedule(
    payload: CreateFeeScheduleRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Publica una tabla de tramos nueva (las salidas ya liquidadas no cambian)."""
    tiers = [FeeTier(t.from_return_pct / _HUNDRED, t.rate_pct / _HUNDRED) for t in payload.tiers]
    result = factory.fee_schedule().create(
        tiers=tiers, note=payload.note, requester_user_id=int(identity["user_id"])
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=fee_schedule_to_dict(result.data),
        msg="Tabla de comisión publicada. Aplica desde la próxima liquidación.",
    )


# ======================================================================
# Reparto entre propietarios
# ======================================================================

@router.get("/commission-shares", status_code=200)
def get_commission_shares(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Reparto vigente (`current`, puede ser null) y sus versiones anteriores."""
    service = factory.commission_shares()
    current = service.current().data
    return build_success_response(
        data={
            "current": commission_shares_to_dict(current) if current else None,
            "history": [commission_shares_to_dict(v) for v in service.history().data],
        }
    )


@router.put("/commission-shares", status_code=200)
def set_commission_shares(
    payload: SetCommissionSharesRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Publica un reparto nuevo entre propietarios (suma 100 %)."""
    shares = [CommissionShare(s.user_id, s.pct / _HUNDRED) for s in payload.shares]
    result = factory.commission_shares().set(
        shares=shares, note=payload.note, requester_user_id=int(identity["user_id"])
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(
        data=commission_shares_to_dict(result.data),
        msg="Reparto guardado. Aplica a las comisiones de las próximas liquidaciones.",
    )


# ======================================================================
# Comisiones recibidas
# ======================================================================

@router.get("/commissions", status_code=200)
def list_owner_earnings(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Comisión acumulada de cada propietario."""
    result = factory.commission_shares().earnings()
    return build_list_response(items=[owner_earning_to_dict(e) for e in result.data])


@router.get("/me/commissions", status_code=200)
def my_commissions(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Las comisiones que recibí, de la más reciente a la más vieja."""
    result = factory.commission_shares().mine(int(identity["user_id"]))
    return build_list_response(items=[commission_credit_to_dict(c) for c in result.data])
