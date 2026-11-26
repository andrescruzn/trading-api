# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/evaluation/evaluate_alerts_service.py
#
# Evalúa las reglas de eventos (señal, orden) en los hooks de M7/M8.
# Las reglas periódicas (precio, P&L, drawdown) las evalúa
# EvaluatePeriodicAlertsService en el ciclo del scheduler.
#
# DISEÑO (fire-and-forget):
# - Si la evaluación falla, se loguea pero NO se propaga la excepción.
# - Las alertas son informativas — nunca bloquean la operación principal.
# ======================================================================

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository
from app.modules.alerts.services.evaluation.fire_alert_service import FireAlertService

if TYPE_CHECKING:
    from app.modules.bots.domain.signal_entity import Signal
    from app.modules.orders.domain.order_entity import Order

logger = logging.getLogger(__name__)


class EvaluateAlertsService:
    """
    Evalúa las reglas de alerta activas contra un contexto dado.

    Puntos de invocación:
    - GenerateSignalService → evaluate_signal_alerts()
    - CreateOrderService    → evaluate_order_alerts()
    """

    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        fire_service: FireAlertService,
    ):
        self._rule_repo = rule_repo
        self._fire = fire_service

    # ------------------------------------------------------------------
    # Señales (M7)
    # ------------------------------------------------------------------

    def evaluate_signal_alerts(self, signal: "Signal", bot_id: int) -> None:
        """
        Evalúa reglas tipo 'signal' para el bot.
        Solo dispara si la señal está aprobada y es buy/sell.
        """
        if not signal.approved or signal.action not in ("buy", "sell"):
            return

        try:
            rules = self._rule_repo.list_active_by_type_and_bot(
                rule_type="signal", bot_id=bot_id
            )
        except Exception as exc:
            logger.error("evaluate_signal_alerts: error cargando reglas: %s", exc)
            return

        for rule in rules:
            try:
                spec = rule.rule_spec
                action_filter = spec.get("action", "any")
                if action_filter != "any" and action_filter != signal.action:
                    continue

                payload: dict[str, Any] = {
                    "signal_id": signal.id,
                    "action": signal.action,
                    "bot_id": bot_id,
                }
                if signal.entry_price is not None:
                    payload["entry_price"] = float(signal.entry_price)
                if signal.confidence is not None:
                    payload["confidence"] = float(signal.confidence)

                self._fire.fire(
                    rule=rule,
                    title=f"Señal {signal.action.upper()} — Bot #{bot_id}",
                    message=(
                        f"Acción: {signal.action.upper()}"
                        + (f" @ {signal.entry_price}" if signal.entry_price else "")
                        + (f" (confianza: {float(signal.confidence):.1%})" if signal.confidence else "")
                    ),
                    severity="info",
                    payload=payload,
                )
            except Exception as exc:
                logger.error("evaluate_signal_alerts: error disparando regla %s: %s", rule.id, exc)

    # ------------------------------------------------------------------
    # Órdenes (M8)
    # ------------------------------------------------------------------

    def evaluate_order_alerts(self, order: "Order", bot_id: int) -> None:
        """
        Evalúa reglas tipo 'error' si la orden fue rechazada,
        o reglas tipo 'signal' (ejecutada) para trazabilidad.
        """
        try:
            if order.status == "rejected":
                rules = self._rule_repo.list_active_by_type_and_bot(
                    rule_type="error", bot_id=bot_id
                )
                for rule in rules:
                    try:
                        self._fire.fire(
                            rule=rule,
                            title=f"Orden RECHAZADA — Bot #{bot_id}",
                            message=f"Orden {order.id} ({order.side} {order.type}) fue rechazada.",
                            severity="warning",
                            payload={"order_id": order.id, "side": order.side, "status": order.status},
                        )
                    except Exception as exc:
                        logger.error("evaluate_order_alerts: rule %s: %s", rule.id, exc)
        except Exception as exc:
            logger.error("evaluate_order_alerts: error: %s", exc)
