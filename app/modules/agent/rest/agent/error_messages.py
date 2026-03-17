# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/agent/error_messages.py
#
# Mensajes de usuario para cada código de error del agente.
# El Service retorna el código; la capa REST decide el mensaje.
# ======================================================================

AGENT_ERROR_MESSAGES: dict[str, str] = {
    "AGENT_STRATEGY_NOT_FOUND": "Estrategia no encontrada.",
    "AGENT_ACCOUNT_NOT_FOUND":  "Cuenta no encontrada.",
    "AGENT_SYMBOL_NOT_FOUND":   "Símbolo no encontrado.",
    "AGENT_TIMEFRAME_NOT_FOUND":"Timeframe no encontrado.",
    "AGENT_NO_CANDLE_DATA":     "No hay velas disponibles para el símbolo y timeframe indicados. Ingesta candles primero.",
    "AGENT_NO_FEATURES":        "No hay features calculados para el símbolo, timeframe y feature_set indicados. Calcula los indicadores primero.",
    "AGENT_NO_BALANCE":         "La cuenta no tiene balance registrado para la moneda base. Registra un balance primero.",
    "AGENT_INVALID_PRICE_RISK": "El precio de entrada y el stop loss son iguales o inválidos.",
    "AGENT_LLM_CALL_FAILED":    "Error al contactar el proveedor de IA. Intenta nuevamente.",
    "AGENT_LLM_PARSE_ERROR":    "La respuesta del modelo de IA no tiene el formato esperado.",
    "AGENT_LLM_MISSING_PRICES": "El modelo de IA no proporcionó precios de entrada/SL/TP.",
}
