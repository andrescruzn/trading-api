# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateDatasetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    symbol_id: int | None = Field(default=None, ge=1)
    timeframe_id: int | None = Field(default=None, ge=1)
    start_ts: datetime | None = Field(default=None)
    end_ts: datetime | None = Field(default=None)
    query_spec: dict[str, Any] = Field(
        default_factory=dict,
        description="Especificación de la consulta para generar el dataset.",
    )
