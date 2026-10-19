# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/signal_decisions/routes.py
#
# ENDPOINTS (aprobación humana de señales, modo `approval`):
# - POST /signals/{signal_id}/approve → ejecuta la orden de la señal
# - POST /signals/{signal_id}/reject  → descarta la señal
#
# Viven en orders (no en bots) porque aprobar = crear la orden, y orders
# ya depende de bots. La cola de pendientes es GET /signals/pending (bots).
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import owner_scope, token_required_actual
from app.extensions.db import get_db
from app.modules.orders.providers import OrderServiceFactory, get_order_factory
from app.modules.orders.services.execution import SignalDecision

from .error_messages import SIGNAL_DECISION_ERROR_MESSAGES

router = APIRouter(prefix="/signals", tags=["Signals"])


def get_factory(db: Session = Depends(get_db)) -> OrderServiceFactory:
    return get_order_factory(db)


def _decision_to_dict(decision: SignalDecision) -> dict[str, Any]:
    signal = decision.signal
    return {
        "signal_id":        signal.id,
        "bot_id":           signal.bot_id,
        "decision_status":  signal.decision_status,
        "decision_channel": signal.decision_channel,
        "decided_at":       signal.decided_at.isoformat() if signal.decided_at else None,
        "order_id":         decision.order.id if decision.order else None,
        "order_status":     decision.order.status if decision.order else None,
    }


# ======================================================================
# POST /signals/{signal_id}/approve
# ======================================================================

@router.post("/{signal_id}/approve", status_code=200)
def approve_signal(
    signal_id: int,
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """Aprueba una señal pendiente: revalida al precio actual y envía la orden."""
    result = factory.execute_signal().execute(
        signal_id,
        owner_id=owner_scope(identity),
        decided_by_user_id=int(identity["user_id"]),
        channel="app",
    )
    if not result.success:
        return build_error_response(result, SIGNAL_DECISION_ERROR_MESSAGES)

    return build_success_response(
        data=_decision_to_dict(result.data),
        msg="Señal aprobada. La orden se envió.",
    )


# ======================================================================
# POST /signals/{signal_id}/reject
# ======================================================================

@router.post("/{signal_id}/reject", status_code=200)
def reject_signal(
    signal_id: int,
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """Rechaza una señal pendiente: no se abre ninguna orden."""
    result = factory.execute_signal().reject(
        signal_id,
        owner_id=owner_scope(identity),
        decided_by_user_id=int(identity["user_id"]),
        channel="app",
    )
    if not result.success:
        return build_error_response(result, SIGNAL_DECISION_ERROR_MESSAGES)

    return build_success_response(
        data=_decision_to_dict(result.data),
        msg="Señal rechazada.",
    )
