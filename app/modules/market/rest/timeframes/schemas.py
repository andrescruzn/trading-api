# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class CreateTimeframeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=8, description="Ej: 1m, 5m, 1h, 1d")
    seconds: int = Field(ge=1, description="Duración en segundos")
