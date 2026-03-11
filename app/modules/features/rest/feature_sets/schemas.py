# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateFeatureSetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(default="1.0.0", max_length=32)
    description: Optional[str] = None
    spec: dict[str, Any] = Field(description="Configuración JSON de los indicadores")
