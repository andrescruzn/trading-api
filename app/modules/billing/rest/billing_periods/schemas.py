# -*- coding: utf-8 -*-

from decimal import Decimal

from pydantic import BaseModel, Field


class OpenBillingPeriodRequest(BaseModel):
    managed_account_id: int = Field(description="ID de la cuenta gestionada")
    opening_equity: Decimal = Field(
        ge=Decimal("0"),
        description="Equity actual de la cuenta al abrir el período",
    )


class CloseBillingPeriodRequest(BaseModel):
    closing_equity: Decimal = Field(
        ge=Decimal("0"),
        description="Equity actual de la cuenta al cerrar el período",
    )
