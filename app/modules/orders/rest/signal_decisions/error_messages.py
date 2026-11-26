# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/signal_decisions/error_messages.py
#
# Aprobar / rechazar una señal: sus propios códigos + los de crear la
# orden (la aprobación termina en CreateOrderService).
# ======================================================================

from app.modules.orders.rest.orders.error_messages import ORDER_ERROR_MESSAGES

SIGNAL_DECISION_ERROR_MESSAGES: dict[str, str] = {
    **ORDER_ERROR_MESSAGES,
    "SIGNAL_NOT_FOUND":       "La señal no existe.",
    "SIGNAL_NOT_ACTIONABLE":  "Solo se pueden aprobar señales de compra o venta que la IA aprobó.",
    "SIGNAL_ALREADY_DECIDED": "Esta señal ya se decidió (desde la app, Telegram o en automático).",
    "SIGNAL_EXPIRED":         "La señal venció sin decisión y ya no se puede ejecutar.",
    "SIGNAL_PRICE_MOVED": (
        "El precio se movió desde que se generó la señal y la operación ya no cumple "
        "el riesgo/beneficio mínimo de 2:1. No se ejecutó."
    ),
    "SIGNAL_POSITION_ALREADY_OPEN": "El agente ya tiene una posición abierta. Ciérrala antes de abrir otra.",
    "SIGNAL_NO_POSITION":     "El agente no tiene una posición que vender.",
}
