# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_fee_settlement_and_equity.py
#
# Marcar comisiones (cobrada / condonada) y equity sugerido desde balances.
# ======================================================================

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.services.billing import SettleFeeTransactionService
from app.modules.billing.services.managed_accounts import EstimateEquityService

D = Decimal
TS = datetime(2026, 10, 20, tzinfo=timezone.utc)


def _fee(status="pending"):
    return FeeTransaction(
        id=3, billing_period_id=1, managed_account_id=1, amount=D("50"), status=status
    )


def _settle_service(fee):
    repo = MagicMock()
    repo.find_by_id.return_value = fee
    repo.update.side_effect = lambda f: f
    return SettleFeeTransactionService(fee_tx_repo=repo), repo


class TestSettleFeeTransactionService:

    def test_charge_marks_charged_with_date(self):
        fee = _fee()
        svc, repo = _settle_service(fee)

        result = svc.execute(fee_tx_id=3, action="charge", notes="Transferencia 123")

        assert result.success is True
        assert fee.status == "charged"
        assert fee.charged_at is not None
        assert fee.notes == "Transferencia 123"
        repo.commit.assert_called_once()

    def test_waive_keeps_note(self):
        fee = _fee()
        svc, _ = _settle_service(fee)

        svc.execute(fee_tx_id=3, action="waive", notes="Cortesía primer mes")

        assert fee.status == "waived"
        assert fee.notes == "Cortesía primer mes"

    def test_only_pending_fees_change(self):
        svc, repo = _settle_service(_fee(status="charged"))

        result = svc.execute(fee_tx_id=3, action="waive")

        assert result.error.code == "FEE_TX_NOT_PENDING"
        assert result.error.http_status == 409
        repo.commit.assert_not_called()

    def test_not_found(self):
        svc, _ = _settle_service(None)

        result = svc.execute(fee_tx_id=9, action="charge")

        assert result.error.code == "FEE_TX_NOT_FOUND"

    def test_invalid_action(self):
        svc, repo = _settle_service(_fee())

        result = svc.execute(fee_tx_id=3, action="delete")

        assert result.error.code == "FEE_TX_INVALID_ACTION"
        repo.find_by_id.assert_not_called()


def _balance(asset, free, locked="0"):
    return SimpleNamespace(asset=asset, free=D(free), locked=D(locked), ts=TS)


def _symbol(symbol_id, base, quote, exchange_id=1):
    return SimpleNamespace(id=symbol_id, base_asset=base, quote_asset=quote, exchange_id=exchange_id)


def _equity_service(balances, symbols, closes):
    """`closes`: symbol_id → último cierre (en el timeframe más corto)."""
    managed_repo = MagicMock()
    managed_repo.find_by_id.return_value = SimpleNamespace(id=1, account_id=7)
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = SimpleNamespace(id=7, base_currency="usdt", exchange_id=1)
    balance_repo = MagicMock()
    balance_repo.list_by_account.return_value = balances
    symbol_repo = MagicMock()
    symbol_repo.list_all.return_value = symbols
    timeframe_repo = MagicMock()
    timeframe_repo.list_all.return_value = [
        SimpleNamespace(id=2, seconds=3600),
        SimpleNamespace(id=1, seconds=60),
    ]
    candle_repo = MagicMock()
    candle_repo.list_candles.side_effect = lambda symbol_id, timeframe_id, limit: (
        [SimpleNamespace(close=closes[symbol_id])]
        if symbol_id in closes and timeframe_id == 1 else []
    )
    svc = EstimateEquityService(
        managed_account_repo=managed_repo,
        account_repo=account_repo,
        balance_repo=balance_repo,
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
        candle_repo=candle_repo,
    )
    return svc, candle_repo


class TestEstimateEquityService:

    def test_values_assets_in_base_currency(self):
        # 1.000 USDT + 0,5 BTC a 60.000 (free 0,4 + locked 0,1) = 31.000
        svc, _ = _equity_service(
            [_balance("USDT", "1000"), _balance("BTC", "0.4", "0.1")],
            [_symbol(10, "BTC", "USDT")],
            {10: "60000"},
        )

        estimate = svc.execute(managed_account_id=1).data

        assert estimate.currency == "USDT"
        assert estimate.equity == D("31000")
        assert estimate.missing == []
        assert estimate.as_of == TS

    def test_uses_latest_record_per_asset(self):
        # La lista viene de la más reciente: el primer USDT es el vigente
        svc, _ = _equity_service(
            [_balance("USDT", "500"), _balance("USDT", "9999")], [], {}
        )

        assert svc.execute(managed_account_id=1).data.equity == D("500")

    def test_asset_without_price_goes_to_missing(self):
        svc, _ = _equity_service(
            [_balance("USDT", "100"), _balance("DOGE", "1000")], [], {}
        )

        estimate = svc.execute(managed_account_id=1).data

        assert estimate.equity == D("100")
        assert estimate.missing == ["DOGE"]

    def test_prefers_pair_on_the_account_exchange(self):
        svc, _ = _equity_service(
            [_balance("ETH", "1")],
            [_symbol(20, "ETH", "USDT", exchange_id=2), _symbol(21, "ETH", "USDT", exchange_id=1)],
            {20: "2000", 21: "2100"},
        )

        assert svc.execute(managed_account_id=1).data.equity == D("2100")

    def test_zero_balances_are_skipped(self):
        svc, _ = _equity_service([_balance("BTC", "0")], [], {})

        estimate = svc.execute(managed_account_id=1).data

        assert estimate.lines == []
        assert estimate.missing == []

    def test_managed_account_not_found(self):
        svc, _ = _equity_service([], [], {})
        svc._managed_account_repo.find_by_id.return_value = None

        result = svc.execute(managed_account_id=99)

        assert result.error.code == "BILLING_MANAGED_ACCOUNT_NOT_FOUND"
