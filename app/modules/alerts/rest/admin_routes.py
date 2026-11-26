# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/admin_routes.py
#
# ENDPOINTS admin:
# - POST /api/alerts/evaluate       → evaluación manual de las reglas de precio
#                                     con un precio dado (mismo antispam que el
#                                     scheduler, que las revisa solas cada ciclo)
#
# La prueba de Telegram pasó a POST /api/notification-settings/telegram/test
# (módulo notifications).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.common.http import send
from app.common.security.jwt.role_guard import super_admin_required
from app.extensions.db import get_db
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory

router = APIRouter(prefix="/alerts", tags=["Alerts Admin"])


def get_factory(db: Session = Depends(get_db)) -> AlertServiceFactory:
    return get_alert_factory(db)


# ======================================================================
# POST /api/alerts/evaluate
# ======================================================================

class EvaluatePriceRequest(BaseModel):
    symbol_id: int = Field(..., gt=0)
    current_price: Decimal = Field(..., gt=0)


@router.post("/evaluate", status_code=200)
def evaluate_price_alerts(
    payload: EvaluatePriceRequest,
    identity: dict = Depends(super_admin_required),
    factory: AlertServiceFactory = Depends(get_factory),
):
    """Evalúa manualmente las reglas tipo 'price' de un símbolo con el precio indicado."""
    report = factory.evaluate_periodic_alerts().evaluate_price(
        symbol_id=payload.symbol_id,
        current_price=payload.current_price,
    ).data
    fired = report.fired
    return send(
        msg=f"Evaluación completada. {fired} alerta(s) disparada(s).",
        status_code=200,
        data={"fired": fired, "checked": report.checked, "cooldown": report.cooldown},
    )

