# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateExchangeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: Literal["crypto_exchange", "broker", "data_vendor"]


class UpdateExchangeRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    type: Optional[Literal["crypto_exchange", "broker", "data_vendor"]] = None
    is_active: Optional[bool] = None


class ExchangeResponse(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    created_at: Optional[datetime]
