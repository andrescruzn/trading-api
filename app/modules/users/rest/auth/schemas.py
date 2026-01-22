# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/schemas.py
#
# CONTRATOS REST (Presentación):
# - POST /users/login
# - POST /users/login/otp/verify
#
# REGLA DE TU API:
# - Envelope:
#   {
#     "msg": "string",
#     "errorCode": <int>,
#     "data": <obj | []>
#   }
#
# NOTA:
# - Login puede devolver:
#   A) token (si password ok)
#   B) otp_required=true (si inicio OTP)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field


# ======================================================================
# Requests
# ======================================================================

class LoginRequest(BaseModel):
    """
    Request para iniciar login.

    Lógica:
    - Si password viene -> login por password
    - Si password NO viene -> login por OTP (envía código)
    """
    email: EmailStr = Field(..., description="User email")
    password: Optional[str] = Field(default=None, description="Optional password for password login")


class VerifyOtpRequest(BaseModel):
    """
    Request para verificar OTP y finalizar login.
    """
    email: EmailStr = Field(..., description="User email")
    otp_code: str = Field(..., min_length=4, max_length=12, description="OTP code sent to email")


# ======================================================================
# Data (Success payloads)
# ======================================================================

class TokenData(BaseModel):
    """
    Data para respuesta exitosa cuando se emite token.
    """
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class OtpRequiredData(BaseModel):
    """
    Data para respuesta exitosa cuando el login requiere OTP.
    """
    otp_required: bool = True
    email: EmailStr
    otp_expires_at: datetime

    # Debug controlado:
    # - En development se puede retornar otp_code.
    # - En production debe ser None.
    otp_code: Optional[str] = None


# ======================================================================
# Responses (Envelope)
# ======================================================================

class LoginResponse(BaseModel):
    """
    Response envelope para /users/login.

    - En éxito:
      - data puede ser TokenData o OtpRequiredData
    - En error:
      - data es []
    """
    msg: str
    errorCode: int
    data: Union[TokenData, OtpRequiredData, List[Any]]


class VerifyOtpResponse(BaseModel):
    """
    Response envelope para /users/login/otp/verify.

    - En éxito:
      - data es TokenData
    - En error:
      - data es []
    """
    msg: str
    errorCode: int
    data: Union[TokenData, List[Any]]