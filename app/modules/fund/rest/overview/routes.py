# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/overview/routes.py
#
# ENDPOINTS (resumen del fondo común, F6):
# - GET /fund/overview    → billetera, capital por agente, saldos, retiros
#                           por pagar, conciliación y ganancias de cada
#                           propietario o socio (staff)
# - GET /fund/me/summary  → lo que gané: comisiones y como inversor (sesión)
#
# El inversor nunca recibe el total de la billetera: /fund/overview es solo
# para el staff.
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_success_response
from app.common.security.jwt import staff_required, token_required_actual
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.serializers import fund_overview_to_dict, participant_summary_to_dict

router = APIRouter(prefix="/fund", tags=["Fund — Overview"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


@router.get("/overview", status_code=200)
def get_fund_overview(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Resumen y conciliación del fondo (super admin y socio)."""
    result = factory.overview().overview()
    return build_success_response(data=fund_overview_to_dict(result.data))


@router.get("/me/summary", status_code=200)
def get_my_summary(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Mis ganancias: realizadas, en los agentes y comisiones recibidas."""
    result = factory.overview().summary(int(identity["user_id"]))
    return build_success_response(data=participant_summary_to_dict(result.data))
