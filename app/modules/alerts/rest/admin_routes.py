# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/admin_routes.py
#
# ENDPOINTS admin:
# - POST /api/alerts/evaluate       → evaluación manual precio/pnl/drawdown
# - POST /api/alerts/test-telegram  → envía mensaje de prueba a Telegram
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import send
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.alerts.channels.telegram_channel import TelegramChannel
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory

router = APIRouter(prefix="/api/alerts", tags=["Alerts Admin"])


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
    identity: dict = Depends(admin_required),
    factory: AlertServiceFactory = Depends(get_factory),
):
    """Evalúa manualmente las reglas tipo 'price' para un símbolo."""
    fired = factory.evaluate_alerts().evaluate_price_alerts(
        symbol_id=payload.symbol_id,
        current_price=payload.current_price,
    )
    return send(
        msg=f"Evaluación completada. {fired} alerta(s) disparada(s).",
        status_code=200,
        data={"fired": fired},
    )


# ======================================================================
# POST /api/alerts/test-telegram
# ======================================================================

@router.post("/test-telegram", status_code=200)
def test_telegram(
    identity: dict = Depends(admin_required),
):
    """Envía un mensaje de prueba al chat Telegram configurado."""
    channel = TelegramChannel(settings=settings)
    ok = channel.send_raw("🤖 Trading AI — Conexión Telegram verificada correctamente.")

    if not ok:
        return send(
            msg="No se pudo enviar el mensaje. Verifica TELEGRAM_BOT_TOKEN y TELEGRAM_DEFAULT_CHAT_ID.",
            status_code=502,
            data={"ok": False},
        )

    return send(msg="Mensaje de prueba enviado exitosamente.", status_code=200, data={"ok": True})
