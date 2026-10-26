# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/funding_entity.py
#
# PROPÓSITO:
# - FundingPayment: un cobro o pago de funding de un perpetuo en live.
#   Binance lo liquida cada pocas horas sobre la posición abierta: positivo
#   = la cuenta recibió, negativo = pagó. No es un fill (no compra ni vende),
#   pero sí mueve dinero: entra al resultado del agente y al flujo de caja
#   del fondo común.
#
# NOTAS:
# - Inmutable: se crea al leerlo del exchange y no se edita.
# - Se asigna al único agente live de esa cuenta en ese símbolo (regla de
#   M7: un agente live por perpetuo y cuenta).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class FundingPayment:
    id: int
    bot_id: int
    account_id: int
    symbol_id: int
    amount: Decimal
    asset: str
    exchange_funding_id: str
    ts: datetime
    created_at: datetime | None = None
