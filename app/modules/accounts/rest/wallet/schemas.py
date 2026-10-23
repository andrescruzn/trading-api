# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/wallet/schemas.py
# ======================================================================

from __future__ import annotations

from pydantic import BaseModel, Field


class SetPlatformWalletRequest(BaseModel):
    account_id: int = Field(..., gt=0, description="Cuenta de exchange que será la billetera.")
