# -*- coding: utf-8 -*-

from decimal import Decimal

from pydantic import BaseModel, Field


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
