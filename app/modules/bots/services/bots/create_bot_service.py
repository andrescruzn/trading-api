# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/create_bot_service.py
#
# Crea un nuevo bot (un "agente" en la UI) vinculando cuenta, símbolo,
# estrategia, timeframe y conjunto de indicadores.
# ======================================================================

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.features.domain.indicator_catalog import is_compatible, outputs_for
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.strategies.domain.strategy_repository import StrategyRepository


class CreateBotService:
    """
    Crea un nuevo bot de trading.

    Reglas de negocio:
    - Estrategia, símbolo activo, timeframe, cuenta y conjunto de
      indicadores deben existir (sin esto la BD respondería con un 500).
    - La cuenta debe ser del usuario (salvo admin) y estar activa.
    - El modo del bot debe coincidir con el de la cuenta: un bot paper no
      opera una cuenta live ni al revés.
    - El conjunto de indicadores debe calcular todo lo que piden las
      reglas de la estrategia.
    - Regla del 1 %: risk_pct en risk_params debe ser > 0 y <= 0.01.
    - El bot siempre inicia en estado 'stopped'.
    """

    def __init__(
        self,
        repo: BotRepository,
        account_repo: AccountRepository,
        strategy_repo: StrategyRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        feature_set_repo: FeatureSetRepository,
    ):
        self._repo = repo
        self._account_repo = account_repo
        self._strategy_repo = strategy_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._feature_set_repo = feature_set_repo

    def create(
        self,
        name: str,
        strategy_id: int,
        symbol_id: int,
        timeframe_id: int,
        account_id: int,
        feature_set_id: int,
        mode: str,
        risk_params: dict[str, Any],
        owner_id: int | None = None,
    ) -> ServiceResult[Bot]:
        """`owner_id=None` = admin: puede crear bots sobre cualquier cuenta."""
        name = name.strip()
        if not name:
            return ServiceResult.fail(code="BOT_INVALID_NAME", http_status=422)

        bot = Bot(
            id=0,
            name=name,
            strategy_id=strategy_id,
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            account_id=account_id,
            feature_set_id=feature_set_id,
            mode=mode,
            status="stopped",
            risk_params=risk_params,
        )

        if not bot.is_valid_mode():
            return ServiceResult.fail(code="BOT_INVALID_MODE", http_status=422)

        if not Bot.is_valid_risk_pct(risk_params.get("risk_pct")):
            return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)

        # ------------------------------------------------------------------
        # Referencias
        # ------------------------------------------------------------------
        account = self._account_repo.get_by_id(account_id)
        if account is None or (owner_id is not None and account.user_id != owner_id):
            return ServiceResult.fail(code="BOT_ACCOUNT_NOT_FOUND", http_status=404)
        if account.status != "active":
            return ServiceResult.fail(code="BOT_ACCOUNT_INACTIVE", http_status=422)
        if account.mode != mode:
            return ServiceResult.fail(
                code="BOT_MODE_ACCOUNT_MISMATCH",
                http_status=422,
                meta={"account_mode": account.mode, "bot_mode": mode},
            )

        strategy = self._strategy_repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(code="BOT_STRATEGY_NOT_FOUND", http_status=404)

        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None or not symbol.is_active:
            return ServiceResult.fail(code="BOT_SYMBOL_NOT_FOUND", http_status=404)

        if self._timeframe_repo.get_by_id(timeframe_id) is None:
            return ServiceResult.fail(code="BOT_TIMEFRAME_NOT_FOUND", http_status=404)

        feature_set = self._feature_set_repo.get_by_id(feature_set_id)
        if feature_set is None:
            return ServiceResult.fail(code="BOT_FEATURE_SET_NOT_FOUND", http_status=404)

        if not is_compatible(strategy.rules, outputs_for(feature_set.spec)):
            return ServiceResult.fail(code="BOT_FEATURE_SET_INCOMPATIBLE", http_status=422)

        created = self._repo.create(bot)
        self._repo.commit()
        return ServiceResult.ok(data=created)
