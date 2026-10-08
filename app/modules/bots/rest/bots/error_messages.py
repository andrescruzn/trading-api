# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Bots (recurso: bots).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# ======================================================================

BOT_ERROR_MESSAGES: dict[str, str] = {
    "BOT_NOT_FOUND":               "El bot no existe.",
    "BOT_INVALID_MODE":            "El modo no es válido. Elige Paper o Live.",
    "BOT_INVALID_RISK_PCT":        "El riesgo por operación debe ser mayor que 0 % y como máximo 100 % (recomendado: 1 %).",
    "BOT_MUST_BE_STOPPED_TO_EDIT": "Detén el bot antes de editarlo.",
    "BOT_INVALID_STATUS":          "El estado no es válido. Elige Activo, Pausado, Detenido o Error.",
    "BOT_INVALID_TRANSITION": (
        "Transición de estado no permitida. "
        "Revisa el estado actual del bot antes de intentar el cambio."
    ),
}
