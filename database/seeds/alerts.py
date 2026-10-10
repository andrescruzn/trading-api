# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/alerts.py
#
# PROPÓSITO:
# - Reglas de alerta de ejemplo del Módulo 9 sobre los agentes demo:
#   señal y drawdown del agente de oro, y error del agente de BTC.
#
# NOTAS:
# - Requiere el seed `bots`. La regla cuyo agente falte se omite.
# - Solo canal de escritorio: así el seed no dispara correos ni mensajes
#   de Telegram reales.
# - Clave natural: (user_id, name).
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.infrastructure.account_model import AccountModel
from app.modules.alerts.infrastructure.alert_rule_model import AlertRuleModel
from app.modules.bots.infrastructure.bot_model import BotModel
from app.modules.users.infrastructure.user_model import UserModel
from database.seeds._helpers import SeedStats, get_or_create

DEMO_USER_EMAIL = "andrescruznovoa@gmail.com"

_DESKTOP_ONLY: dict[str, Any] = {
    "email": False,
    "telegram": False,
    "webhook": False,
    "desktop": True,
}

# (nombre de la regla, agente, rule_type, rule_spec)
ALERT_RULES: list[tuple[str, str, str, dict[str, Any]]] = [
    ("Oro — señal de compra o venta", "Oro — tendencia 4h", "signal", {"action": "any"}),
    ("Oro — drawdown mayor al 5 %", "Oro — tendencia 4h", "drawdown", {"threshold": 5.0}),
    ("BTC — agente con error", "BTC — tendencia 1h", "error", {}),
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    user = session.execute(
        select(UserModel).filter_by(email=DEMO_USER_EMAIL)
    ).scalar_one_or_none()
    if user is None:
        stats.notes.append(f"omitido: no existe el usuario {DEMO_USER_EMAIL}")
        return stats

    for name, bot_name, rule_type, rule_spec in ALERT_RULES:
        bot = session.execute(
            select(BotModel)
            .join(AccountModel, AccountModel.id == BotModel.account_id)
            .where(AccountModel.user_id == user.id, BotModel.name == bot_name)
        ).scalars().first()
        if bot is None:
            stats.notes.append(f"omitida '{name}': no existe el agente '{bot_name}'")
            continue

        get_or_create(
            session,
            AlertRuleModel,
            lookup={"user_id": user.id, "name": name},
            values={
                "bot_id": bot.id,
                "rule_type": rule_type,
                "rule_spec": rule_spec,
                "channels": _DESKTOP_ONLY,
                "is_active": True,
            },
            stats=stats,
        )

    return stats
