# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateModelRunRequest(BaseModel):
    model_id: int = Field(..., ge=1)
    params: dict[str, Any] = Field(default_factory=dict)
    dataset_id: int | None = Field(default=None, ge=1)
    logs_uri: str | None = Field(default=None, max_length=512)


class FinishModelRunRequest(BaseModel):
    status: str = Field(..., description="success | failed")
    metrics: dict[str, Any] = Field(default_factory=dict)
    logs_uri: str | None = Field(default=None, max_length=512)
