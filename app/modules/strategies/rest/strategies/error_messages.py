# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes de error para el módulo Strategies (recurso: strategies).
# Los servicios usan códigos estables; aquí se definen los textos UI.
# ======================================================================

STRATEGY_ERROR_MESSAGES: dict[str, str] = {
    "STRATEGY_NOT_FOUND":             "La estrategia no existe.",
    "STRATEGY_DUPLICATE_NAME_VERSION": "Ya existe una estrategia con ese nombre y versión.",
    "STRATEGY_INVALID_TYPE":          (
        "Tipo de estrategia inválido. "
        "Valores permitidos: trend_following, mean_reversion."
    ),
    "STRATEGY_INCOHERENT_REGIME": (
        "El régimen requerido no es compatible con el tipo de estrategia. "
        "trend_following acepta trend_up o trend_down. "
        "mean_reversion acepta sideways."
    ),
}
