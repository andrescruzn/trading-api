# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/execution_mode_rules.py
#
# Reglas del modo de ejecución de un agente, compartidas por crear y
# editar:
# - execution_mode válido (manual | approval | auto).
# - No hay variable de entorno que apague lo real: un agente real puede ir
#   en cualquier modo (decidido el 2026-10-26).
# - approval/auto exigen un timeframe ≥ SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS:
#   un análisis de IA por vela de 1m dispararía el coste.
# ======================================================================

from __future__ import annotations

from app.common.config import settings
from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot


def check_execution_mode(bot: Bot, timeframe_seconds: int | None) -> ServiceResult[None]:
    if not bot.is_valid_execution_mode():
        return ServiceResult.fail(code="BOT_INVALID_EXECUTION_MODE", http_status=422)

    if bot.approval_ttl_minutes is not None and not 1 <= bot.approval_ttl_minutes <= 1440:
        return ServiceResult.fail(code="BOT_INVALID_APPROVAL_TTL", http_status=422)

    if (
        bot.is_automated()
        and timeframe_seconds is not None
        and timeframe_seconds < settings.SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS
    ):
        return ServiceResult.fail(
            code="BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION",
            http_status=422,
            meta={"min_seconds": settings.SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS},
        )

    return ServiceResult.ok(data=None)
