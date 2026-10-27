# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/demo_capital.py
#
# Monto de los agentes demo (dinero simulado).
#
# Un agente demo opera sobre su propia cuenta de práctica interna: el
# monto que se escribió al crearlo queda como su balance inicial (de ahí
# sale el capital del 1 %) y también en `meta["demo_capital"]` de esa
# cuenta, para mostrarlo sin buscar el primer balance.
# ======================================================================

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot

DEMO_CAPITAL_META_KEY = "demo_capital"


def attach_demo_capital(bots: list[Bot], account_repo: AccountRepository) -> list[Bot]:
    """Completa `bot.demo_capital` en los agentes demo (los reales quedan en None)."""
    for bot in bots:
        if bot.mode != "paper" or bot.account_id is None:
            continue
        account = account_repo.get_by_id(bot.account_id)
        raw = account.meta.get(DEMO_CAPITAL_META_KEY) if account else None
        try:
            bot.demo_capital = Decimal(str(raw)) if raw is not None else None
        except (InvalidOperation, ValueError):
            bot.demo_capital = None
    return bots
