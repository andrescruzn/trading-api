# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/bot_access.py
#
# PROPÓSITO:
# - Regla de propiedad de los bots, compartida por los servicios de bots
#   y de señales: un usuario solo ve y opera los bots de sus cuentas.
#
# NOTAS:
# - `owner_id=None` significa "sin restricción" (admin).
# - Un bot ajeno se trata igual que uno inexistente (BOT_NOT_FOUND) para
#   no revelar qué IDs existen.
# ======================================================================

from __future__ import annotations

from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


def find_accessible_bot(
    bot_repo: BotRepository,
    account_repo: AccountRepository,
    bot_id: int,
    owner_id: int | None,
) -> Bot | None:
    """Devuelve el bot si existe y `owner_id` puede verlo; si no, None."""
    bot = bot_repo.get_by_id(bot_id)
    if bot is None or owner_id is None:
        return bot
    if bot.account_id is None:
        return None
    account = account_repo.get_by_id(bot.account_id)
    if account is None or account.user_id != owner_id:
        return None
    return bot
