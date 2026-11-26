# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Strategies (recurso: strategies).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# ======================================================================

STRATEGY_ERROR_MESSAGES: dict[str, str] = {
    "STRATEGY_NOT_FOUND":             "La estrategia no existe.",
    "STRATEGY_DUPLICATE_NAME_VERSION": "Ya existe una estrategia con ese nombre y versión.",
    "STRATEGY_INVALID_TYPE":          (
        "El tipo de estrategia no es válido. "
        "Elige Seguimiento de tendencia o Reversión a la media."
    ),
    "STRATEGY_INCOHERENT_REGIME": (
        "El régimen no encaja con el tipo de estrategia: "
        "Seguimiento de tendencia opera en tendencia alcista o bajista, "
        "y Reversión a la media en mercado lateral."
    ),
}
