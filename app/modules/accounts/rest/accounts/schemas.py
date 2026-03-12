# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120, description="Nombre descriptivo de la cuenta")
    mode: Literal["paper", "live"] = Field(description="Modo de operación")
    exchange_id: Optional[int] = Field(default=None, description="ID del exchange asociado")
    base_currency: str = Field(default="USD", max_length=16, description="Moneda base")
    api_key: Optional[str] = Field(default=None, description="API key del exchange (se cifra)")
    api_secret: Optional[str] = Field(default=None, description="API secret del exchange (se cifra)")
    credentials_label: Optional[str] = Field(
        default=None, max_length=255, description="Etiqueta descriptiva de las credenciales"
    )


class UpdateAccountRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[Literal["active", "suspended"]] = None
    exchange_id: Optional[int] = None
    base_currency: Optional[str] = Field(default=None, max_length=16)
    api_key: Optional[str] = Field(default=None, description="Nueva API key (re-cifra las anteriores)")
    api_secret: Optional[str] = Field(default=None, description="Nuevo API secret")
    credentials_label: Optional[str] = Field(default=None, max_length=255)


class AccountResponse(BaseModel):
    id: int
    user_id: int
    exchange_id: Optional[int]
    name: str
    mode: str
    base_currency: str
    status: str
    credentials_ref: Optional[str]
    has_credentials: bool
    meta: dict[str, Any]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
