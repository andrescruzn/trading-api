# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/orders/schemas.py
#
# Schemas Pydantic para validar el request body de órdenes.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class CreateOrderRequest(BaseModel):
    """
    Payload para crear y ejecutar una orden.

    Reglas de validación:
    - bot_id   : requerido, > 0
    - side     : "buy" o "sell"
    - type     : "market", "limit", "stop" o "stop_limit"
    - qty      : cantidad de activo a operar, > 0
    - price    : requerido si type es "limit" o "stop_limit"
    - stop_price: requerido si type es "stop" o "stop_limit"
    - signal_id: opcional — vincula la orden a una señal generada por el bot
    """

    bot_id:        int     = Field(..., gt=0)
    side:          str     = Field(..., pattern="^(buy|sell)$")
    type:          str     = Field(..., pattern="^(market|limit|stop|stop_limit)$")
    qty:           Decimal = Field(..., gt=0)
    price:         Decimal | None = Field(default=None, gt=0)
    stop_price:    Decimal | None = Field(default=None, gt=0)
    time_in_force: str     | None = Field(default=None, pattern="^(GTC|IOC|FOK)$")
    signal_id:     int     | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_price_consistency(self) -> "CreateOrderRequest":
        """
        Valida que los precios requeridos estén presentes según el tipo de orden.
        Pydantic llama este validador después de construir el modelo.
        """
        if self.type in ("limit", "stop_limit") and self.price is None:
            raise ValueError(
                f"Las órdenes de tipo '{self.type}' requieren el campo 'price'."
            )
        if self.type in ("stop", "stop_limit") and self.stop_price is None:
            raise ValueError(
                f"Las órdenes de tipo '{self.type}' requieren el campo 'stop_price'."
            )
        return self
