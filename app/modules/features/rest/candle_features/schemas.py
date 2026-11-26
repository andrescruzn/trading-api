# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CalculateFeaturesRequest(BaseModel):
    symbol_id: int = Field(ge=1)
    timeframe_id: int = Field(ge=1)
    feature_set_id: int = Field(ge=1)
    from_ts: Optional[datetime] = None
    to_ts: Optional[datetime] = None
