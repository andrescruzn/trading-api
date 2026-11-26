# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/recommendations/error_messages.py
#
# Mensajes de usuario para cada código de error de las recomendaciones
# de mercados. El Service retorna el código; la capa REST decide el texto.
# ======================================================================

RECOMMENDATION_ERROR_MESSAGES: dict[str, str] = {
    "EXPLORER_TIMEFRAME_MISSING": (
        "Falta el timeframe diario (1d) en el catálogo, así que no hay ranking que analizar."
    ),
    "RECOMMENDATION_NO_CANDIDATES": (
        "No hay mercados alcistas o laterales con datos suficientes para recomendar. "
        "Actualiza los datos del explorador o prueba con otra clase de activo."
    ),
    "RECOMMENDATION_NO_STRATEGIES": (
        "No hay estrategias que puedan operar compras. Crea una estrategia alcista o de rango primero."
    ),
    "RECOMMENDATION_LLM_CALL_FAILED": "No pudimos contactar a la IA. Inténtalo de nuevo en unos minutos.",
    "RECOMMENDATION_LLM_PARSE_ERROR": "La IA respondió en un formato inesperado. Inténtalo de nuevo.",
    "RECOMMENDATION_EMPTY": (
        "La IA no dio recomendaciones que cumplan las reglas de la app. Inténtalo de nuevo."
    ),
}
