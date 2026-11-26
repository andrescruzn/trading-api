# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/rest/notification_settings/schemas.py
# ======================================================================

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UpdateTelegramSettingsRequest(BaseModel):
    enabled: bool
    # Vacío o ausente = conservar el token guardado (la API nunca lo devuelve)
    bot_token: str | None = Field(default=None, max_length=128)
    default_chat_id: str | None = Field(default=None, max_length=64)
    updates_mode: Literal["off", "polling", "webhook"] = "off"
    webhook_url: str | None = Field(default=None, max_length=2048)


class UpdateEmailSettingsRequest(BaseModel):
    enabled: bool
