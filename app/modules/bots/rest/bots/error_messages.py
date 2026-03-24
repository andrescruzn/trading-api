# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: bots).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# ======================================================================

BOT_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":               "El bot no existe.",
    "BOT_INVALID_MODE":            "Modo inválido. Valores permitidos: paper, live.",
    "BOT_INVALID_RISK_PCT":        "El campo risk_pct debe ser un número entre 0 y 1 (ej: 0.01 = 1%).",
    "BOT_MUST_BE_STOPPED_TO_EDIT": "Solo se puede editar un bot en estado 'stopped'.",
    "BOT_INVALID_STATUS":          "Estado inválido. Valores permitidos: running, stopped, paused, error.",
    "BOT_INVALID_TRANSITION": (
        "Transición de estado no permitida. "
        "Revisa el estado actual del bot antes de intentar el cambio."
    ),
}
