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
    role_code: Literal["user", "admin", "investor"] = Field(default="user")


class UpdateUserRoleRequest(BaseModel):
    role_code: Literal["user", "admin", "investor"] = Field(
        ..., description="Rol nuevo: user, admin o investor."
    )


class UpdateUserStatusRequest(BaseModel):
    status: Literal["active", "blocked", "disabled"] = Field(
        ...,
        description=(
            "Estado nuevo: active (puede entrar), blocked (suspensión temporal) "
            "o disabled (cuenta que ya no se usa)."
        ),
    )
