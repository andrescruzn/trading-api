# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateSymbolRequest(BaseModel):
    exchange_id: int = Field(ge=1)
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: Literal["crypto", "metal", "etf", "stock", "forex"]
    base_asset: Optional[str] = Field(default=None, max_length=32)
    quote_asset: Optional[str] = Field(default=None, max_length=32)
    tick_size: Optional[Decimal] = None
    lot_size: Optional[Decimal] = None


class UpdateSymbolRequest(BaseModel):
    asset_class: Optional[Literal["crypto", "metal", "etf", "stock", "forex"]] = None
    base_asset: Optional[str] = Field(default=None, max_length=32)
    quote_asset: Optional[str] = Field(default=None, max_length=32)
    tick_size: Optional[Decimal] = None
    lot_size: Optional[Decimal] = None
    is_active: Optional[bool] = None


class SymbolResponse(BaseModel):
    id: int
    exchange_id: int
    symbol: str
    asset_class: str
    base_asset: Optional[str]
    quote_asset: Optional[str]
    tick_size: Optional[str]
    lot_size: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
