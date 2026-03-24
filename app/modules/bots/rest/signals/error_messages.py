# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: signals).
# ======================================================================

SIGNAL_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":             "El bot no existe.",
    "BOT_NOT_ACTIVE":            "El bot debe estar en estado 'running' para generar señales.",
    "BOT_NO_FEATURE_SET":        "El bot no tiene un feature set configurado.",
    "SIGNAL_INVALID_ACTION_FILTER": (
        "Filtro de acción inválido. Valores permitidos: buy, sell, hold."
    ),
    # Errores del Agente (M6) que pueden propagarse
    "AGENT_STRATEGY_NOT_FOUND":  "La estrategia del bot no existe.",
    "AGENT_ACCOUNT_NOT_FOUND":   "La cuenta del bot no existe.",
    "AGENT_SYMBOL_NOT_FOUND":    "El símbolo del bot no existe.",
    "AGENT_TIMEFRAME_NOT_FOUND": "El timeframe del bot no existe.",
    "AGENT_NO_CANDLE_DATA":      "No hay datos de velas disponibles para este símbolo y timeframe.",
    "AGENT_NO_FEATURES":         "No hay features calculadas para este símbolo y timeframe.",
    "AGENT_NO_BALANCE":          "La cuenta no tiene balance disponible.",
    "AGENT_LLM_CALL_FAILED":     "El servicio de IA no está disponible en este momento.",
    "AGENT_LLM_PARSE_ERROR":     "El servicio de IA devolvió una respuesta inválida.",
    "AGENT_LLM_MISSING_PRICES":  "El servicio de IA no devolvió los precios requeridos.",
    "AGENT_INVALID_PRICE_RISK":  "Los niveles de precio calculados son inválidos.",
}
