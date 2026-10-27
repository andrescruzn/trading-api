# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_risk_gate_service.py
#
# Tests unitarios del RiskGateService (M8).
#
# ESTRATEGIA:
# - Repositorios MagicMock; sin BD.
# - Los flags de settings se parchean con monkeypatch sobre el mismo
#   objeto `settings` que importa el módulo del servicio.
#
# CUBRE:
# - Kill switch (TRADING_ENABLED); no hay interruptor aparte para live.
# - Notional máximo: min(ORDER_MAX_NOTIONAL, risk_params.max_notional).
# - Drawdown máximo → BOT_MAX_DRAWDOWN_REACHED y bot en `error`.
# - Las ventas no se bloquean por notional ni drawdown.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.services.risk import risk_gate_service as risk_module
from app.modules.orders.services.risk.risk_gate_service import RiskGateService


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(
    mode: str = "paper",
    status: str = "running",
    risk_params: dict | None = None,
) -> Bot:
    return Bot(
        id=1,
        name="Agente de prueba",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode=mode,
        status=status,
        risk_params=risk_params if risk_params is not None else {"risk_pct": 0.01},
    )


def _make_position(realized_pnl: str) -> Position:
    return Position(id=1, bot_id=1, symbol_id=5, realized_pnl=Decimal(realized_pnl))


def _make_service(
    realized_pnls: list[str] | None = None,
    free_balance: str | None = "900",
    account_exists: bool = True,
):
    """Retorna (service, bot_repo, account_repo, balance_repo, position_repo)."""
    bot_repo = MagicMock()
    account_repo = MagicMock()
    balance_repo = MagicMock()
    position_repo = MagicMock()

    position_repo.list_by_bot.return_value = [
        _make_position(p) for p in (realized_pnls or [])
    ]

    if account_exists:
        account = MagicMock()
        account.id = 2
        account.base_currency = "USDT"
        account_repo.get_by_id.return_value = account
    else:
        account_repo.get_by_id.return_value = None

    if free_balance is None:
        balance_repo.get_latest_by_asset.return_value = None
    else:
        balance = MagicMock()
        balance.free = Decimal(free_balance)
        balance_repo.get_latest_by_asset.return_value = balance

    service = RiskGateService(
        bot_repo=bot_repo,
        account_repo=account_repo,
        balance_repo=balance_repo,
        position_repo=position_repo,
    )
    return service, bot_repo, account_repo, balance_repo, position_repo


@pytest.fixture(autouse=True)
def _default_settings(monkeypatch):
    """Valores conocidos para no depender del .env del entorno."""
    monkeypatch.setattr(risk_module.settings, "TRADING_ENABLED", True)
    monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 10000.0)


# ======================================================================
# TestKillSwitch
# ======================================================================

class TestKillSwitch:

    @pytest.mark.parametrize("side", ["buy", "sell"])
    def test_trading_disabled_blocks_any_side(self, monkeypatch, side):
        monkeypatch.setattr(risk_module.settings, "TRADING_ENABLED", False)
        service, *_ = _make_service()

        result = service.check(_make_bot(), side, Decimal("1"), Decimal("100"))

        assert result.success is False
        assert result.error.code == "TRADING_DISABLED"
        assert result.error.http_status == 503

    def test_trading_disabled_blocks_live_too(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "TRADING_ENABLED", False)
        service, *_ = _make_service()

        result = service.check(_make_bot(mode="live"), "sell", Decimal("1"), Decimal("100"))

        assert result.error.code == "TRADING_DISABLED"


# ======================================================================
# TestRealAndDemo
# ======================================================================

class TestRealAndDemo:

    @pytest.mark.parametrize("mode", ["live", "paper"])
    def test_real_and_demo_agents_pass_without_any_live_switch(self, mode):
        service, *_ = _make_service()

        result = service.check(_make_bot(mode=mode), "buy", Decimal("1"), Decimal("100"))

        assert result.success is True


# ======================================================================
# TestNotionalCap
# ======================================================================

class TestNotionalCap:

    def test_buy_above_global_cap_fails(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 1000.0)
        service, *_ = _make_service()

        # 2 × 600 = 1200 > 1000
        result = service.check(_make_bot(), "buy", Decimal("2"), Decimal("600"))

        assert result.success is False
        assert result.error.code == "ORDER_NOTIONAL_TOO_HIGH"
        assert result.error.http_status == 422
        assert Decimal(result.error.meta["notional"]) == Decimal("1200")
        assert Decimal(result.error.meta["max"]) == Decimal("1000")

    def test_buy_exactly_at_cap_passes(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 1000.0)
        service, *_ = _make_service()

        result = service.check(_make_bot(), "buy", Decimal("2"), Decimal("500"))

        assert result.success is True

    def test_bot_cap_smaller_than_global_applies(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 1000.0)
        bot = _make_bot(risk_params={"risk_pct": 0.01, "max_notional": 300})
        service, *_ = _make_service()

        # 400 ≤ 1000 global pero > 300 del bot
        result = service.check(bot, "buy", Decimal("4"), Decimal("100"))

        assert result.success is False
        assert result.error.code == "ORDER_NOTIONAL_TOO_HIGH"
        assert Decimal(result.error.meta["max"]) == Decimal("300")

    def test_global_cap_smaller_than_bot_applies(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 500.0)
        bot = _make_bot(risk_params={"risk_pct": 0.01, "max_notional": 5000})
        service, *_ = _make_service()

        result = service.check(bot, "buy", Decimal("6"), Decimal("100"))

        assert result.success is False
        assert Decimal(result.error.meta["max"]) == Decimal("500")

    def test_zero_global_cap_means_no_global_limit(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 0)
        service, *_ = _make_service()

        result = service.check(_make_bot(), "buy", Decimal("1000"), Decimal("1000"))

        assert result.success is True

    def test_zero_global_cap_still_applies_bot_cap(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 0)
        bot = _make_bot(risk_params={"risk_pct": 0.01, "max_notional": 300})
        service, *_ = _make_service()

        result = service.check(bot, "buy", Decimal("4"), Decimal("100"))

        assert result.success is False
        assert Decimal(result.error.meta["max"]) == Decimal("300")

    def test_sell_is_not_blocked_by_notional(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 100.0)
        bot = _make_bot(risk_params={"risk_pct": 0.01, "max_notional": 50})
        service, *_ = _make_service()

        result = service.check(bot, "sell", Decimal("10"), Decimal("1000"))

        assert result.success is True


# ======================================================================
# TestDrawdown
# ======================================================================

class TestDrawdown:

    def _bot(self, max_dd: float, status: str = "running") -> Bot:
        return _make_bot(status=status, risk_params={"risk_pct": 0.01, "max_drawdown_pct": max_dd})

    def test_drawdown_reached_fails_and_sets_bot_error(self):
        # Pérdida 100, saldo 900 → capital 1000 → drawdown 10 % ≥ 10 %
        bot = self._bot(0.10)
        service, bot_repo, *_ = _make_service(realized_pnls=["-60", "-40"], free_balance="900")

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.success is False
        assert result.error.code == "BOT_MAX_DRAWDOWN_REACHED"
        assert result.error.http_status == 409
        assert result.error.meta["max_drawdown_pct"] == 0.10
        assert bot.status == "error"
        bot_repo.update.assert_called_once_with(bot)
        bot_repo.commit.assert_called_once()

    def test_drawdown_below_limit_passes(self):
        # Drawdown 10 % < 20 %
        bot = self._bot(0.20)
        service, bot_repo, *_ = _make_service(realized_pnls=["-100"], free_balance="900")

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.success is True
        assert bot.status == "running"
        bot_repo.update.assert_not_called()
        bot_repo.commit.assert_not_called()

    def test_net_positive_realized_pnl_never_reaches_drawdown(self):
        bot = self._bot(0.01)
        service, _, account_repo, *_ = _make_service(realized_pnls=["-50", "80"])

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.success is True
        account_repo.get_by_id.assert_not_called()

    def test_without_balance_any_loss_reaches_drawdown(self):
        # Sin saldo: capital = pérdida → drawdown 100 %
        bot = self._bot(0.50)
        service, *_ = _make_service(realized_pnls=["-10"], free_balance=None)

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.error.code == "BOT_MAX_DRAWDOWN_REACHED"

    def test_without_account_drawdown_is_not_evaluated(self):
        bot = self._bot(0.01)
        service, *_ = _make_service(realized_pnls=["-500"], account_exists=False)

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.success is True

    def test_without_max_drawdown_pct_is_not_evaluated(self):
        bot = _make_bot(risk_params={"risk_pct": 0.01})
        service, _, _, _, position_repo = _make_service(realized_pnls=["-900"])

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.success is True
        position_repo.list_by_bot.assert_not_called()

    def test_sell_is_not_blocked_by_drawdown(self):
        bot = self._bot(0.01)
        service, bot_repo, _, _, position_repo = _make_service(
            realized_pnls=["-900"], free_balance="100",
        )

        result = service.check(bot, "sell", Decimal("1"), Decimal("100"))

        assert result.success is True
        assert bot.status == "running"
        position_repo.list_by_bot.assert_not_called()
        bot_repo.commit.assert_not_called()

    def test_bot_that_cannot_go_to_error_still_fails_without_update(self):
        # paused → error no es una transición válida: se rechaza sin tocar el bot
        bot = self._bot(0.10, status="paused")
        service, bot_repo, *_ = _make_service(realized_pnls=["-100"], free_balance="900")

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.error.code == "BOT_MAX_DRAWDOWN_REACHED"
        assert bot.status == "paused"
        bot_repo.update.assert_not_called()
        bot_repo.commit.assert_not_called()

    def test_notional_is_checked_before_drawdown(self, monkeypatch):
        monkeypatch.setattr(risk_module.settings, "ORDER_MAX_NOTIONAL", 50.0)
        bot = self._bot(0.10)
        service, bot_repo, *_ = _make_service(realized_pnls=["-100"], free_balance="900")

        result = service.check(bot, "buy", Decimal("1"), Decimal("100"))

        assert result.error.code == "ORDER_NOTIONAL_TOO_HIGH"
        assert bot.status == "running"
        bot_repo.commit.assert_not_called()
