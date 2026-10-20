# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CapitalMovementRequest(BaseModel):
    kind: Literal["deposit", "withdrawal"] = Field(description="Aporte o retiro")
    amount: Decimal = Field(gt=Decimal("0"), max_digits=30, decimal_places=12)
    ts: datetime | None = Field(default=None, description="Cuándo entró o salió (por defecto, ahora)")
    notes: str | None = Field(default=None, max_length=500)


class CreateManagedAccountRequest(BaseModel):
    investor_id: int = Field(description="ID del inversor")
    account_id: int = Field(description="ID de la cuenta de trading (M4)")
    name: str = Field(min_length=2, max_length=120, description="Nombre descriptivo")
    initial_capital: Decimal = Field(ge=Decimal("0"), description="Capital inicial aportado")
    period_type: str = Field(default="monthly", description="Frecuencia: daily | weekly | monthly")
    bot_id: int | None = Field(default=None, description="Bot que opera la cuenta (opcional)")


class UpdateManagedAccountRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    bot_id: int | None = Field(default=None)
    period_type: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
