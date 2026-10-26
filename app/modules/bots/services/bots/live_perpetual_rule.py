# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/live_perpetual_rule.py
#
# REGLA (perpetuos en live, 2026-10-26):
# - Un solo agente live por símbolo perpetuo en la misma cuenta. Binance
#   suma en UNA posición todo lo que se opera en un símbolo de futuros y
#   cobra el funding a esa posición: con dos agentes, la venta de uno
#   cerraría lo del otro y el funding no se podría repartir.
# - Cuenta cualquier estado (detenido incluido): un agente detenido puede
#   seguir teniendo una posición abierta en el exchange.
# ======================================================================

from __future__ import annotations

from app.modules.bots.domain.bot_repository import BotRepository


def perpetual_taken_by_other(
    repo: BotRepository, *, account_id: int, symbol_id: int, bot_id: int | None = None
) -> bool:
    """True si otro agente live de la cuenta ya opera ese perpetuo."""
    return any(
        other.mode == "live" and other.symbol_id == symbol_id and other.id != bot_id
        for other in repo.list_by_account(int(account_id))
    )
