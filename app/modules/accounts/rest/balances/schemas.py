# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RecordBalanceRequest(BaseModel):
    asset: str = Field(min_length=1, max_length=32, description="Símbolo del activo (USDT, BTC...)")
    free: Decimal = Field(ge=Decimal("0"), description="Saldo disponible")
    locked: Decimal = Field(ge=Decimal("0"), description="Saldo bloqueado en órdenes")


class BalanceResponse(BaseModel):
    id: int
    account_id: int
    asset: str
    free: str          # Decimal serializado como string para precisión
    locked: str
    total: str
    ts: Optional[datetime]
