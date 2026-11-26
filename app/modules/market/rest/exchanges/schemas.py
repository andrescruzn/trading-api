# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExchangeResponse(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    created_at: Optional[datetime]
