# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: signals).
# En la UI los bots se llaman "agentes".
# ======================================================================

SIGNAL_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":             "No encontramos ese agente.",
    "BOT_NOT_ACTIVE":            "Inicia el agente para poder analizar el mercado.",
    "BOT_NO_FEATURE_SET":        "El agente no tiene un conjunto de indicadores, así que no hay nada que evaluar.",
    "SIGNAL_INVALID_ACTION_FILTER": (
        "Filtro de acción inválido. Valores permitidos: buy, sell, hold."
    ),
    # Errores del análisis (M6) que pueden propagarse
    "AGENT_STRATEGY_NOT_FOUND":  "La estrategia del agente ya no existe.",
    "AGENT_ACCOUNT_NOT_FOUND":   "La cuenta del agente ya no existe.",
    "AGENT_SYMBOL_NOT_FOUND":    "El símbolo del agente ya no existe.",
    "AGENT_TIMEFRAME_NOT_FOUND": "El timeframe del agente ya no existe.",
    "AGENT_NO_CANDLE_DATA": (
        "Aún no hay velas para este símbolo. El agente las descarga solo cuando está activo; "
        "espera un par de minutos e inténtalo de nuevo."
    ),
    "AGENT_NO_FEATURES": (
        "Los indicadores aún se están calculando. Espera un par de minutos e inténtalo de nuevo."
    ),
    "AGENT_FEATURE_SET_INCOMPATIBLE": (
        "El conjunto de indicadores del agente no calcula todo lo que pide su estrategia."
    ),
    "AGENT_NO_BALANCE": (
        "La cuenta del agente no tiene saldo en su moneda base. Regístralo en Mis cuentas."
    ),
    "AGENT_LLM_CALL_FAILED":     "No pudimos contactar a la IA. Inténtalo de nuevo en unos minutos.",
    "AGENT_LLM_PARSE_ERROR":     "La IA respondió en un formato inesperado. Inténtalo de nuevo.",
    "AGENT_LLM_MISSING_PRICES":  "La IA no propuso entrada, stop loss y take profit. Inténtalo de nuevo.",
    "AGENT_INVALID_PRICE_RISK": (
        "La entrada y el stop loss son iguales, así que no se puede calcular el tamaño de la posición."
    ),
}
