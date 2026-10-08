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
    "AGENT_NO_CANDLE_DATA":     "No hay velas guardadas para ese símbolo y timeframe. Descárgalas primero en Descargar velas.",
    "AGENT_NO_FEATURES":        "No hay indicadores calculados para ese símbolo, timeframe y feature set. Calcúlalos primero.",
    "AGENT_NO_BALANCE":         "La cuenta no tiene balance en su moneda base. Registra un balance en Mis cuentas primero.",
    "AGENT_INVALID_PRICE_RISK": "La entrada y el stop loss son iguales o no son válidos, así que no se puede calcular el tamaño de la posición.",
    "AGENT_LLM_CALL_FAILED":    "No pudimos contactar al proveedor de IA. Inténtalo de nuevo en unos minutos.",
    "AGENT_LLM_PARSE_ERROR":    "El agente de IA respondió en un formato inesperado. Inténtalo de nuevo.",
    "AGENT_LLM_MISSING_PRICES": "El agente de IA no propuso entrada, stop loss y take profit. Inténtalo de nuevo.",
}
