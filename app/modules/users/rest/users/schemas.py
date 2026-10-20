# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/schemas.py
# ======================================================================

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UpdateUserRoleRequest(BaseModel):
    role_code: Literal["user", "admin", "investor"] = Field(
        ..., description="Rol nuevo: user, admin o investor."
    )
