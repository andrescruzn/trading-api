# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/evaluation/evaluate_alerts_service.py
#
# Evalúa las reglas activas contra un contexto dado (señal, orden, precio).
#
# DISEÑO (fire-and-forget):
# - Si la evaluación falla, se loguea pero NO se propaga la excepción.
# - Las alertas son informativas — nunca bloquean la operación principal.
# ======================================================================

from __future__ import annotations

import logging
from decimal import Decimal
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
    - Endpoint manual       → evaluate_price_alerts()
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

    # ------------------------------------------------------------------
    # Precio (endpoint manual)
    # ------------------------------------------------------------------

    def evaluate_price_alerts(self, symbol_id: int, current_price: Decimal) -> int:
        """
        Evalúa reglas tipo 'price' para un símbolo.
        Retorna el número de alertas disparadas.
        """
        fired = 0
        try:
            rules = self._rule_repo.list_active_by_type_and_bot(rule_type="price")
            for rule in rules:
                try:
                    spec = rule.rule_spec
                    if spec.get("symbol_id") != symbol_id:
                        continue

                    operator = spec.get("operator", "lt")
                    threshold = Decimal(str(spec.get("threshold", 0)))
                    matches = self._eval_operator(current_price, operator, threshold)

                    if matches:
                        self._fire.fire(
                            rule=rule,
                            title=f"Precio {operator.upper()} {threshold}",
                            message=f"Precio actual {current_price} {operator} {threshold}",
                            severity="warning",
                            payload={
                                "symbol_id": symbol_id,
                                "current_price": float(current_price),
                                "threshold": float(threshold),
                                "operator": operator,
                            },
                        )
                        fired += 1
                except Exception as exc:
                    logger.error("evaluate_price_alerts: rule %s: %s", rule.id, exc)
        except Exception as exc:
            logger.error("evaluate_price_alerts: error: %s", exc)
        return fired

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _eval_operator(value: Decimal, operator: str, threshold: Decimal) -> bool:
        ops = {
            "lt":  lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "gt":  lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "eq":  lambda v, t: v == t,
        }
        fn = ops.get(operator)
        return fn(value, threshold) if fn else False
