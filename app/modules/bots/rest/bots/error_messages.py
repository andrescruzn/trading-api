# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: bots).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# En la UI los bots se llaman "agentes".
# ======================================================================

BOT_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":               "No encontramos ese agente.",
    "BOTS_INVALID_FILTER":         "Algún filtro no es válido. Elige el estado y el modo de la lista.",
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
    "BOT_PERPETUAL_LIVE_TAKEN": (
        "Ya hay un agente live en ese perpetuo con esta cuenta. Binance une la posición de "
        "un símbolo de futuros, así que solo puede operarlo un agente: usa el que ya existe "
        "o elige otro símbolo."
    ),
    "BOT_TIMEFRAME_NOT_FOUND":     "No encontramos ese timeframe.",
    "BOT_FEATURE_SET_NOT_FOUND":   "No encontramos ese conjunto de indicadores.",
    "BOT_FEATURE_SET_INCOMPATIBLE": (
        "Ese conjunto de indicadores no calcula todo lo que pide la estrategia. "
        "Elige uno compatible."
    ),
    "BOT_INVALID_EXECUTION_MODE":  "Elige cómo actúa el agente: Manual, Con aprobación o Automático.",
    "BOT_INVALID_APPROVAL_TTL":    "El tiempo para aprobar debe estar entre 1 minuto y 24 horas.",
    "BOT_AUTO_LIVE_DISABLED": (
        "El modo Automático no está habilitado para cuentas live. "
        "Usa Con aprobación o una cuenta paper."
    ),
    "BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION": (
        "Los modos Con aprobación y Automático necesitan un timeframe de 15 minutos o más."
    ),

    # Señales compartidas (POST/DELETE /bots/{id}/subscription)
    "SUBSCRIPTION_OWN_BOT":        "Este agente es tuyo: sus señales ya las ves en la app.",
    "SUBSCRIPTION_TELEGRAM_REQUIRED": (
        "Las señales compartidas llegan por Telegram. Conéctalo desde el menú de "
        "tu usuario → Conectar Telegram y vuelve a intentarlo."
    ),

    # Actualizar datos del agente (POST /bots/{id}/market/sync)
    "SYMBOL_NOT_FOUND":            "No encontramos el símbolo de este agente.",
    "TIMEFRAME_NOT_FOUND":         "No encontramos el timeframe de este agente.",
    "FEATURE_SET_NOT_FOUND":       "No encontramos el conjunto de indicadores de este agente.",
    "EXCHANGE_NOT_FOUND":          "No encontramos el exchange del símbolo de este agente.",
    "EXCHANGE_NOT_SUPPORTED_CCXT": "No podemos descargar velas de este exchange automáticamente.",
    "CCXT_SYMBOL_NOT_FOUND":       "El exchange ya no ofrece el símbolo de este agente.",
    "CCXT_NETWORK_ERROR":          "No pudimos conectar con el exchange. Intenta de nuevo en un momento.",
    "CCXT_FETCH_ERROR":            "El exchange no devolvió las velas. Intenta de nuevo en un momento.",
    "CANDLES_EMPTY_PAYLOAD":       "El exchange no devolvió velas para este símbolo y timeframe.",
    "INSUFFICIENT_CANDLES": (
        "Descargamos las velas, pero aún no alcanzan para calcular los indicadores "
        "(se necesitan al menos 220)."
    ),
}
