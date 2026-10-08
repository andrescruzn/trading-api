# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/orders/error_messages.py
#
# Mapeo de códigos de error estables → mensajes de UI en español.
# Los servicios solo retornan códigos; los mensajes se definen aquí.
# ======================================================================

ORDER_ERROR_MESSAGES: dict[str, str] = {
    "ORDER_NOT_FOUND":          "La orden no existe.",
    "ORDER_INVALID_SIDE":       "Elige Compra o Venta.",
    "ORDER_INVALID_TYPE":       "El tipo de orden no es válido. Elige Mercado, Límite, Stop o Stop límite.",
    "ORDER_INVALID_QTY":        "La cantidad debe ser mayor a cero.",
    "ORDER_PRICE_REQUIRED":     "Las órdenes Límite y Stop límite necesitan un precio límite.",
    "ORDER_STOP_PRICE_REQUIRED":"Las órdenes Stop y Stop límite necesitan un precio de activación.",
    "ORDER_EXECUTION_FAILED":   "No se pudo ejecutar la orden. Revisa la configuración del bot y del exchange.",
    "BOT_NOT_FOUND":            "El bot no existe.",
    "BOT_NOT_RUNNING":          "Inicia el bot para poder enviar órdenes.",
    "SYMBOL_NOT_FOUND":         "El símbolo asociado al bot no existe.",
    "FILLS_MISSING_FILTER":     "Elige un bot o una orden para ver sus ejecuciones.",
}
