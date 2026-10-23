# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/schemas.py
# ======================================================================

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InviteUserRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    # Super admin no se invita: los propietarios se definen por seed.
    role_code: Literal["partner", "investor"] = Field(default="investor")


class UpdateUserRoleRequest(BaseModel):
    role_code: Literal["partner", "investor"] = Field(
        ..., description="Rol nuevo: partner (socio, solo lectura) o investor."
    )


class UpdateUserStatusRequest(BaseModel):
    status: Literal["active", "blocked", "disabled"] = Field(
        ...,
        description=(
            "Estado nuevo: active (puede entrar), blocked (suspensión temporal) "
            "o disabled (cuenta que ya no se usa)."
        ),
    )
