# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/schemas.py
#
# Requests del fondo común. Los montos llegan como Decimal (el front los
# envía como texto para no perder precisión).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.fund.domain.fund_settings_entity import (
    MAX_DEPOSIT_REQUEST_TTL_HOURS,
    MAX_MIN_HOLD_DAYS,
)


class UpdateFundSettingsRequest(BaseModel):
    min_hold_days: int = Field(..., ge=0, le=MAX_MIN_HOLD_DAYS)
    deposit_auto_confirm_max: Decimal = Field(..., ge=0, max_digits=30, decimal_places=12)
    deposit_request_ttl_hours: int = Field(..., ge=1, le=MAX_DEPOSIT_REQUEST_TTL_HOURS)


class NetworkChoiceRequest(BaseModel):
    network: str = Field(..., min_length=1, max_length=32)
    name: str | None = Field(default=None, max_length=64)
    # Solo con billetera paper: en live la dirección se lee del exchange
    address: str | None = Field(default=None, max_length=255)
    tag: str | None = Field(default=None, max_length=128)


class SetDepositNetworksRequest(BaseModel):
    networks: list[NetworkChoiceRequest] = Field(default_factory=list, max_length=10)


class CreateDepositRequest(BaseModel):
    network: str = Field(..., min_length=1, max_length=32)
    txid: str = Field(..., min_length=10, max_length=128)
    amount: Decimal = Field(..., gt=0, max_digits=30, decimal_places=12)


class ConfirmDepositRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=12)
    note: str | None = Field(default=None, max_length=500)


class RejectDepositRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=500)


class AssignUnclaimedRequest(BaseModel):
    txid: str = Field(..., min_length=1, max_length=128)
    user_id: int = Field(..., gt=0)
    note: str = Field(..., min_length=1, max_length=500)


class OpenPoolRequest(BaseModel):
    bot_id: int = Field(..., gt=0)


class QueueAllocationRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0, max_digits=30, decimal_places=12)
    source_bucket: str = Field(default="pending", pattern="^(pending|available)$")


class SettleRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class RefundRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=30, decimal_places=12)
    reason: str = Field(..., min_length=5, max_length=500)
