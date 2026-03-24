# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/orders/error_messages.py
#
# Mapeo de códigos de error estables → mensajes de UI en español.
# Los servicios solo retornan códigos; los mensajes se definen aquí.
# ======================================================================

ORDER_ERROR_MESSAGES: dict[str, str] = {
    "ORDER_NOT_FOUND":          "La orden no existe.",
    "ORDER_INVALID_SIDE":       "Lado inválido. Valores permitidos: buy, sell.",
    "ORDER_INVALID_TYPE":       "Tipo de orden inválido. Valores permitidos: market, limit, stop, stop_limit.",
    "ORDER_INVALID_QTY":        "La cantidad debe ser mayor a cero.",
    "ORDER_PRICE_REQUIRED":     "Las órdenes limit y stop_limit requieren el campo 'price'.",
    "ORDER_STOP_PRICE_REQUIRED":"Las órdenes stop y stop_limit requieren el campo 'stop_price'.",
    "ORDER_EXECUTION_FAILED":   "No se pudo ejecutar la orden. Revisa la configuración del bot y del exchange.",
    "BOT_NOT_FOUND":            "El bot no existe.",
    "BOT_NOT_RUNNING":          "El bot debe estar en estado 'running' para aceptar órdenes.",
    "SYMBOL_NOT_FOUND":         "El símbolo asociado al bot no existe.",
    "FILLS_MISSING_FILTER":     "Debes indicar order_id o bot_id para listar fills.",
}
