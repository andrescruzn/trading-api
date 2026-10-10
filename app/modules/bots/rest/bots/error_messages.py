# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: bots).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# En la UI los bots se llaman "agentes".
# ======================================================================

BOT_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":               "No encontramos ese agente.",
    "BOT_INVALID_NAME":            "Escribe un nombre para el agente.",
    "BOT_INVALID_MODE":            "El modo no es válido. Elige Paper o Live.",
    "BOT_INVALID_RISK_PCT":        "El riesgo por operación debe ser mayor que 0 % y como máximo 1 % del capital.",
    "BOT_MUST_BE_STOPPED_TO_EDIT": "Detén el agente antes de cambiar su configuración.",
    "BOT_INVALID_STATUS":          "El estado no es válido. Elige Activo, Pausado, Detenido o Error.",
    "BOT_INVALID_TRANSITION": (
        "El agente no puede pasar a ese estado desde el actual. "
        "Recarga la página para ver su estado."
    ),
    "BOT_ACCOUNT_NOT_FOUND":       "No encontramos esa cuenta entre las tuyas.",
    "BOT_ACCOUNT_INACTIVE":        "La cuenta está suspendida. Elige una cuenta activa.",
    "BOT_MODE_ACCOUNT_MISMATCH":   "El modo del agente debe ser el mismo de la cuenta (paper o live).",
    "BOT_STRATEGY_NOT_FOUND":      "No encontramos esa estrategia.",
    "BOT_SYMBOL_NOT_FOUND":        "Ese símbolo no existe o está desactivado.",
    "BOT_TIMEFRAME_NOT_FOUND":     "No encontramos ese timeframe.",
    "BOT_FEATURE_SET_NOT_FOUND":   "No encontramos ese conjunto de indicadores.",
    "BOT_FEATURE_SET_INCOMPATIBLE": (
        "Ese conjunto de indicadores no calcula todo lo que pide la estrategia. "
        "Elige uno compatible."
    ),
}
