# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# Límite de claves en los JSON libres (evita payloads gigantes en la BD)
_MAX_JSON_KEYS = 20


class CreateAlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., pattern="^(price|signal|pnl|drawdown|error)$")
    rule_spec: dict[str, Any] = Field(default_factory=dict, max_length=_MAX_JSON_KEYS)
    channels: dict[str, Any] = Field(default_factory=dict, max_length=_MAX_JSON_KEYS)
    bot_id: int | None = Field(default=None, gt=0)


class UpdateAlertRuleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    rule_spec: dict[str, Any] | None = Field(default=None, max_length=_MAX_JSON_KEYS)
    channels: dict[str, Any] | None = Field(default=None, max_length=_MAX_JSON_KEYS)
    is_active: bool | None = None
