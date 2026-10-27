# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/create_bot_service.py
#
# Crea un nuevo bot (un "agente" en la UI) sobre un símbolo, estrategia,
# timeframe y conjunto de indicadores. Hay dos tipos que conviven:
# - real (`live`): opera la billetera única de Binance.
# - demo (`paper`): dinero simulado con el monto que se escribe al crearlo.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.demo_capital import DEMO_CAPITAL_META_KEY
from app.modules.bots.services.bots.execution_mode_rules import check_execution_mode
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.features.domain.indicator_catalog import is_compatible, outputs_for
from app.modules.bots.services.bots.live_perpetual_rule import perpetual_taken_by_other
from app.modules.market.domain.ccxt_exchanges import is_perpetual
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.strategies.domain.strategy_repository import StrategyRepository

# Tope del monto simulado: evita cifras absurdas que rompan el DECIMAL(30,12)
MAX_DEMO_CAPITAL = Decimal("1000000000")


class CreateBotService:
    """
    Crea un nuevo bot de trading.

    Reglas de negocio:
    - Estrategia, símbolo activo, timeframe y conjunto de indicadores deben
      existir (sin esto la BD respondería con un 500).
    - Agente real (`live`): siempre sobre la billetera única de Binance
      (se asegura aquí); no lleva monto: su capital sale de su pool en el
      fondo. Un perpetuo (`XAU/USDT:USDT`) en real: uno solo por símbolo
      (Binance une la posición y el funding del símbolo).
    - Agente demo (`paper`): exige un monto > 0. Se le crea una cuenta de
      práctica interna con ese monto como balance inicial, en la moneda de
      cotización del símbolo; no toca la billetera ni el fondo.
    - El conjunto de indicadores debe calcular todo lo que piden las
      reglas de la estrategia.
    - Regla del 1 %: risk_pct en risk_params debe ser > 0 y <= 0.01.
    - El bot siempre inicia en estado 'stopped'.
    """

    def __init__(
        self,
        repo: BotRepository,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        strategy_repo: StrategyRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        feature_set_repo: FeatureSetRepository,
        ensure_wallet: Callable[[], Account | None],
    ):
        self._repo = repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._strategy_repo = strategy_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._feature_set_repo = feature_set_repo
        self._ensure_wallet = ensure_wallet

    def create(
        self,
        name: str,
        strategy_id: int,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        mode: str,
        risk_params: dict[str, Any],
        requester_user_id: int,
        demo_capital: Decimal | None = None,
        execution_mode: str = "manual",
        approval_ttl_minutes: int | None = None,
    ) -> ServiceResult[Bot]:
        name = name.strip()
        if not name:
            return ServiceResult.fail(code="BOT_INVALID_NAME", http_status=422)

        bot = Bot(
            id=0,
            name=name,
            strategy_id=strategy_id,
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            account_id=None,
            feature_set_id=feature_set_id,
            mode=mode,
            status="stopped",
            risk_params=risk_params,
            execution_mode=execution_mode,
            approval_ttl_minutes=approval_ttl_minutes,
        )

        if not bot.is_valid_mode():
            return ServiceResult.fail(code="BOT_INVALID_MODE", http_status=422)

        if not Bot.is_valid_risk_pct(risk_params.get("risk_pct")):
            return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)

        if mode == "paper":
            if demo_capital is None or not 0 < demo_capital <= MAX_DEMO_CAPITAL:
                return ServiceResult.fail(code="BOT_INVALID_DEMO_CAPITAL", http_status=422)
        elif demo_capital is not None:
            return ServiceResult.fail(code="BOT_DEMO_CAPITAL_ONLY_DEMO", http_status=422)

        # ------------------------------------------------------------------
        # Referencias
        # ------------------------------------------------------------------
        strategy = self._strategy_repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(code="BOT_STRATEGY_NOT_FOUND", http_status=404)

        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None or not symbol.is_active:
            return ServiceResult.fail(code="BOT_SYMBOL_NOT_FOUND", http_status=404)

        timeframe = self._timeframe_repo.get_by_id(timeframe_id)
        if timeframe is None:
            return ServiceResult.fail(code="BOT_TIMEFRAME_NOT_FOUND", http_status=404)

        execution_check = check_execution_mode(bot, timeframe.seconds)
        if not execution_check.success:
            return execution_check

        feature_set = self._feature_set_repo.get_by_id(feature_set_id)
        if feature_set is None:
            return ServiceResult.fail(code="BOT_FEATURE_SET_NOT_FOUND", http_status=404)

        if not is_compatible(strategy.rules, outputs_for(feature_set.spec)):
            return ServiceResult.fail(code="BOT_FEATURE_SET_INCOMPATIBLE", http_status=422)

        # ------------------------------------------------------------------
        # Dinero: billetera de Binance (real) o cuenta de práctica (demo)
        # ------------------------------------------------------------------
        if mode == "live":
            wallet_account = self._ensure_wallet()
            if wallet_account is None:
                return ServiceResult.fail(code="BOT_WALLET_UNAVAILABLE", http_status=409)
            if is_perpetual(symbol.symbol) and perpetual_taken_by_other(
                self._repo, account_id=wallet_account.id, symbol_id=symbol.id
            ):
                return ServiceResult.fail(code="BOT_PERPETUAL_LIVE_TAKEN", http_status=409)
            bot.account_id = wallet_account.id

        try:
            if mode == "paper":
                bot.account_id = self._create_demo_account(
                    name, symbol.quote_asset, demo_capital, requester_user_id
                ).id
            created = self._repo.create(bot)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        created.demo_capital = demo_capital
        return ServiceResult.ok(data=created)

    def _create_demo_account(
        self, bot_name: str, quote_asset: str | None, capital: Decimal, user_id: int
    ) -> Account:
        """Cuenta de práctica del agente demo con su monto como balance inicial (sin commit)."""
        asset = (quote_asset or "USDT").upper()
        account = self._account_repo.create(
            Account(
                id=0,
                user_id=int(user_id),
                name=f"Demo · {bot_name}"[:120],
                mode="paper",
                base_currency=asset,
                status="active",
                meta={DEMO_CAPITAL_META_KEY: str(capital)},
            )
        )
        self._balance_repo.record(
            AccountBalance(
                id=0,
                account_id=account.id,
                asset=asset,
                free=capital,
                locked=Decimal("0"),
                ts=utc_now(),
            )
        )
        return account
