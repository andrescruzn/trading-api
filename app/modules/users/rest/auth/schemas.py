# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/schemas.py
#
# Schemas Pydantic (REST / presentación).
#
# CONTRATO DEL API (envelope):
# {
#   "msg": "string",
#   "errorCode": <int>,
#   "data": <obj | []>
# }
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Union

from pydantic import BaseModel, EmailStr, Field


# ======================================================================
# Request
# ======================================================================

class LoginOtpRequest(BaseModel):
    """
    Request: solicitar OTP por email.
    """
    email: EmailStr = Field(..., description="User email")


# ======================================================================
# Data del caso de uso (éxito)
# ======================================================================

class LoginOtpData(BaseModel):
    """
    Payload que va dentro de `data` en un 200 OK.

    Nota:
    - otp_code es TEMPORAL (solo dev mientras no hay email real).
    """
    email: EmailStr
    otp_code: str
    otp_expires_at: datetime


# ======================================================================
# Envelope de respuesta del endpoint
# ======================================================================

class LoginOtpResponse(BaseModel):
    """
    Response envelope para el endpoint /users/login.
    - En éxito: data es LoginOtpData
    - En error: data es []
    """
    msg: str
    errorCode: int
    data: Union[LoginOtpData, List[Any]]