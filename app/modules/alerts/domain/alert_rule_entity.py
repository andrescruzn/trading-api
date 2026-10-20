# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/domain/alert_rule_entity.py
#
# Entidad de dominio: AlertRule.
# Regla de alerta configurada por un usuario o asociada a un bot.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.common.security.url_guard import is_allowed_webhook_url


class AlertRule:
    """
    Entidad de dominio: AlertRule.

    Tipos de regla (rule_type):
    - price     : el precio de un símbolo cruza un umbral
    - signal    : el bot genera una señal de cierto tipo (buy/sell/hold/any)
    - pnl       : el P&L del bot supera/baja de un umbral
    - drawdown  : el drawdown del bot supera un umbral
    - error     : el bot entra en estado de error

    Canales (channels JSON):
    {
        "email":    true | false,
        "telegram": true | false,
        "webhook":  "https://..." | false,
        "desktop":  true | false
    }

    rule_spec por tipo:
    - price:    {"symbol_id": 1, "operator": "lt|gt|lte|gte", "threshold": 80000}
    - signal:   {"action": "buy|sell|hold|any"}
    - pnl:      {"threshold": -5.0, "period": "daily|total"}   (% del capital invertido)
    - drawdown: {"threshold": 10.0}                            (% del capital invertido)
    - error:    {}

    price, pnl y drawdown se revisan solas en cada ciclo del scheduler
    (EvaluatePeriodicAlertsService); pnl y drawdown exigen `bot_id`.
    """

    VALID_TYPES = ("price", "signal", "pnl", "drawdown", "error")
    BOT_REQUIRED_TYPES = ("pnl", "drawdown")

    def __init__(
        self,
        id: int,
        name: str,
        rule_type: str,
        rule_spec: dict[str, Any],
        channels: dict[str, Any],
        is_active: bool = True,
        user_id: int | None = None,
        bot_id: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.rule_type = rule_type
        self.rule_spec = rule_spec
        self.channels = channels
        self.is_active = is_active
        self.user_id = user_id
        self.bot_id = bot_id
        self.created_at = created_at

    def is_valid_type(self) -> bool:
        return self.rule_type in self.VALID_TYPES

    def wants_email(self) -> bool:
        return bool(self.channels.get("email"))

    def wants_telegram(self) -> bool:
        return bool(self.channels.get("telegram"))

    def wants_webhook(self) -> str | None:
        url = self.channels.get("webhook")
        return url if is_allowed_webhook_url(url) else None

    def has_valid_webhook(self) -> bool:
        """Sin webhook es válido; si hay uno, debe ser https y no interno (SSRF)."""
        url = self.channels.get("webhook")
        return not url or is_allowed_webhook_url(url)

    def wants_desktop(self) -> bool:
        return bool(self.channels.get("desktop"))
