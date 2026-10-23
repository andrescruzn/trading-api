# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/settings/routes.py
#
# ENDPOINTS (ajustes del fondo común):
# - GET /fund/settings                     → ajustes completos (staff)
# - PUT /fund/settings                     → permanencia, tope y vencimiento (super admin)
# - GET /fund/settings/networks/available  → redes del exchange para la moneda (super admin)
# - PUT /fund/settings/networks            → redes aceptadas con su dirección (super admin)
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import staff_required, super_admin_required
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import SetDepositNetworksRequest, UpdateFundSettingsRequest
from app.modules.fund.rest.serializers import available_network_to_dict, settings_to_dict
from app.modules.fund.services.settings import NetworkChoice

router = APIRouter(prefix="/fund/settings", tags=["Fund — Settings"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


@router.get("", status_code=200)
def get_fund_settings(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Ajustes del fondo (super admin y socio)."""
    result = factory.fund_settings().get()
    return build_success_response(data=settings_to_dict(result.data))


@router.put("", status_code=200)
def update_fund_settings(
    payload: UpdateFundSettingsRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Cambia permanencia mínima, tope de confirmación automática y vencimiento (super admin)."""
    result = factory.fund_settings().update(
        min_hold_days=payload.min_hold_days,
        deposit_auto_confirm_max=payload.deposit_auto_confirm_max,
        deposit_request_ttl_hours=payload.deposit_request_ttl_hours,
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=settings_to_dict(result.data), msg="Ajustes guardados.")


@router.get("/networks/available", status_code=200)
def list_available_networks(
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Redes del exchange para la moneda del fondo (super admin)."""
    result = factory.deposit_networks().list_available()
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    data = result.data
    return build_success_response(
        data={
            "asset":    data.asset,
            "is_live":  data.is_live,
            "networks": [available_network_to_dict(n) for n in data.networks],
        }
    )


@router.put("/networks", status_code=200)
def set_deposit_networks(
    payload: SetDepositNetworksRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Guarda las redes aceptadas; en live la dirección se lee del exchange (super admin)."""
    result = factory.deposit_networks().set(
        [NetworkChoice(n.network, n.name, n.address, n.tag) for n in payload.networks],
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=settings_to_dict(result.data), msg="Redes guardadas.")
