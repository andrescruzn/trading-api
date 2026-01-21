# -*- coding: utf-8 -*-

# ======================================================================
# app/common/http_responder.py
#
# PROPÓSITO:
# - Responder SIEMPRE con el contrato estándar del API:
#   {
#     "msg": "...",
#     "errorCode": <http_status>,
#     "data": ...
#   }
#
# REGLA:
# - Esto es UI/presentación => debe vivir en common/rest utils.
# ======================================================================

from __future__ import annotations

from typing import Any
from fastapi.responses import JSONResponse


def send(*, msg: str, status_code: int, data: Any) -> JSONResponse:
    """
    Construye una respuesta JSON estándar.

    Nota:
    - status_code debe ser el HTTP status real.
    - data nunca debe ser None (normalizamos a []).
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "msg": msg,
            "errorCode": status_code,
            "data": data if data is not None else [],
        },
    )