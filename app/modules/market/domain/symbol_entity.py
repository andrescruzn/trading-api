# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/symbol_entity.py
#
# Entidad de dominio: Symbol (par/activo por exchange).
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional


class Symbol:
    """
    Entidad de dominio: Symbol.

    Representa un par o activo negociable asociado a un exchange.
    Clases válidas: crypto | metal | etf | stock | forex
    """

    VALID_ASSET_CLASSES = ("crypto", "metal", "etf", "stock", "forex")

    def __init__(
        self,
        id: int,
        exchange_id: int,
        symbol: str,
        asset_class: str,
        base_asset: Optional[str] = None,
        quote_asset: Optional[str] = None,
        tick_size: Optional[Decimal] = None,
        lot_size: Optional[Decimal] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        exchange_name: Optional[str] = None,
    ):
        self.id = id
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.asset_class = asset_class
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.tick_size = tick_size
        self.lot_size = lot_size
        self.is_active = is_active
        self.created_at = created_at
        self.exchange_name = exchange_name

    def activate(self) -> None:
        """Activa el símbolo para operar."""
        self.is_active = True

    def deactivate(self) -> None:
        """Desactiva el símbolo (no se pueden crear bots con él)."""
        self.is_active = False

    def is_valid_asset_class(self) -> bool:
        """Verifica que el asset_class es uno de los valores permitidos."""
        return self.asset_class in self.VALID_ASSET_CLASSES
