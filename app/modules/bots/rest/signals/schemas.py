# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/signals/schemas.py
# ======================================================================

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateSignalRequest(BaseModel):
    bot_id: int = Field(..., gt=0, description="ID del bot para el que se genera la señal.")
