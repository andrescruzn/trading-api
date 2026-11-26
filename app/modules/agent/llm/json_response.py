# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/json_response.py
#
# Lectura de respuestas JSON del LLM.
#
# NOTAS:
# - Los servicios del pool no usan "modo JSON": el formato se pide en el
#   prompt y la respuesta puede venir envuelta en un bloque ```json.
# - Se rechazan NaN/Infinity (json.loads los acepta por defecto).
# - AnalyzeService conserva su propio parser (exige `decision`); este es
#   el genérico para casos de uso nuevos.
# ======================================================================

from __future__ import annotations

import json
from typing import Any

from app.modules.agent.llm.llm_client import LLMParseError


def _reject_json_constant(name: str) -> None:
    raise ValueError(f"Valor no permitido en la respuesta del LLM: {name}")


def parse_json_object(raw: str) -> dict[str, Any]:
    """
    Devuelve el objeto JSON de la respuesta del LLM.

    Raises:
        LLMParseError: si no es JSON válido o no es un objeto.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Quitar la primera línea (```json o ```) y la última (```)
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

    try:
        data = json.loads(cleaned, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LLMParseError(raw_response=raw, detail=str(exc)) from exc

    if not isinstance(data, dict):
        raise LLMParseError(raw_response=raw, detail="La respuesta del LLM no es un objeto JSON.")
    return data
