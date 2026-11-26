# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    version: str = Field(default="1.0.0", max_length=32)
    model_type: str = Field(
        ...,
        description="xgboost | lightgbm | sklearn | nn",
    )
    feature_set_id: int | None = Field(default=None, ge=1)
    artifact_uri: str | None = Field(default=None, max_length=512)
    meta: dict[str, Any] = Field(default_factory=dict)


class UpdateModelRequest(BaseModel):
    status: str | None = Field(
        default=None,
        description="active | deprecated | archived",
    )
    artifact_uri: str | None = Field(default=None, max_length=512)
    meta: dict[str, Any] | None = Field(default=None)
