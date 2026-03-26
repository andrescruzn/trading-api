# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateAlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., pattern="^(price|signal|pnl|drawdown|error)$")
    rule_spec: dict[str, Any] = Field(default_factory=dict)
    channels: dict[str, Any] = Field(default_factory=dict)
    bot_id: int | None = None


class UpdateAlertRuleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    rule_spec: dict[str, Any] | None = None
    channels: dict[str, Any] | None = None
    is_active: bool | None = None
