# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/orders/error_messages.py
#
# Mapeo de códigos de error estables → mensajes de UI en español.
# Los servicios solo retornan códigos; los mensajes se definen aquí.
# ======================================================================

ORDER_ERROR_MESSAGES: dict[str, str] = {
    "ORDER_NOT_FOUND":          "La orden no existe.",
    "ORDERS_MISSING_BOT":       "Elige un agente para ver sus órdenes.",
    "ORDER_INVALID_SIDE":       "Elige Compra o Venta.",
    "ORDER_INVALID_TYPE":       "El tipo de orden no es válido. Elige Mercado, Límite, Stop o Stop límite.",
    "ORDER_INVALID_QTY":        "La cantidad debe ser mayor a cero.",
    "ORDER_PRICE_REQUIRED":     "Las órdenes Límite y Stop límite necesitan un precio límite.",
    "ORDER_STOP_PRICE_REQUIRED":"Las órdenes Stop y Stop límite necesitan un precio de activación.",
    "ORDER_NO_MARKET_PRICE":    "Todavía no hay velas de este símbolo para calcular el precio. Espera a que se descarguen.",
    "ORDER_SELL_EXCEEDS_POSITION": "No puedes vender más de lo que tiene la posición del agente. En spot no se abren ventas en corto.",
    "ORDER_NOTIONAL_TOO_HIGH":  "La orden supera el valor máximo permitido por operación. Reduce la cantidad.",
    "ORDER_SIGNAL_MISMATCH":    "La orden no coincide con la señal: la señal debe estar aprobada y tener la misma dirección.",
    "ORDER_SIGNAL_ALREADY_USED":"Esta señal ya tiene una orden. Cada señal se ejecuta una sola vez.",
    "ORDER_EXECUTION_FAILED":   "El exchange no aceptó la orden. Quedó registrada como rechazada; revisa la cuenta y el saldo.",
    "ORDER_EXECUTION_UNCERTAIN":"No recibimos respuesta del exchange. Revisa la orden en el exchange antes de reintentar.",
    "SIGNAL_NOT_FOUND":         "La señal no existe o no es de este agente.",
    "ORDER_NATIVE_STOP_ACTIVE": (
        "El stop loss de esta posición está en el exchange y no se pudo cancelar "
        "(puede que ya se haya ejecutado). Espera unos minutos a que se sincronice."
    ),
    "TRADING_DISABLED":         "El envío de órdenes está detenido temporalmente por el administrador.",
    "TRADING_LIVE_DISABLED":    "Las órdenes en modo live están desactivadas. Por ahora solo se ejecutan órdenes paper.",
    "BOT_MAX_DRAWDOWN_REACHED": "El agente alcanzó su pérdida máxima y se detuvo para proteger el capital. Revísalo antes de volver a operar.",
    "BOT_NOT_FOUND":            "El agente no existe.",
    "BOT_NOT_RUNNING":          "Inicia el agente para poder enviar órdenes.",
    "SYMBOL_NOT_FOUND":         "El símbolo asociado al agente no existe.",
    "FILLS_MISSING_FILTER":     "Elige un agente o una orden para ver sus ejecuciones.",
}
