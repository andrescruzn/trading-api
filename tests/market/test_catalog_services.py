# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_catalog_services.py
#
# CRUD de los catálogos de M2 (exchanges, símbolos, timeframes):
# validaciones, códigos de error, http_status y commit solo en éxito.
# Sin BD: repositorios MagicMock.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.timeframe_entity import Timeframe
from app.modules.market.services.exchanges import (
    CreateExchangeService,
    ListExchangesService,
    UpdateExchangeService,
)
from app.modules.market.services.symbols import (
    CreateSymbolService,
    ListSymbolsService,
    UpdateSymbolService,
)
from app.modules.market.services.timeframes import CreateTimeframeService, ListTimeframesService


def _repo() -> MagicMock:
    repo = MagicMock()
    repo.create.side_effect = lambda entity: entity
    repo.update.side_effect = lambda entity: entity
    return repo


def _assert_failed(result, code: str, http_status: int, repo: MagicMock) -> None:
    assert result.success is False
    assert result.error.code == code
    assert result.error.http_status == http_status
    repo.commit.assert_not_called()


# ======================================================================
# Exchanges
# ======================================================================

class TestCreateExchangeService:

    def test_creates_active_exchange_and_commits(self):
        repo = _repo()
        repo.get_by_name.return_value = None

        result = CreateExchangeService(repo).create(name="Kraken", type="crypto_exchange")

        assert result.success is True
        assert (result.data.name, result.data.type, result.data.is_active) == ("Kraken", "crypto_exchange", True)
        repo.create.assert_called_once()
        repo.commit.assert_called_once()

    def test_rejects_invalid_type_with_422(self):
        repo = _repo()

        result = CreateExchangeService(repo).create(name="Banco", type="bank")

        _assert_failed(result, "EXCHANGE_INVALID_TYPE", 422, repo)
        repo.create.assert_not_called()

    def test_rejects_duplicate_name_with_409(self):
        repo = _repo()
        repo.get_by_name.return_value = Exchange(id=1, name="Binance", type="crypto_exchange")

        result = CreateExchangeService(repo).create(name="Binance", type="crypto_exchange")

        _assert_failed(result, "EXCHANGE_NAME_EXISTS", 409, repo)
        repo.create.assert_not_called()


class TestUpdateExchangeService:

    def _make(self, current: Exchange | None, by_name: Exchange | None = None):
        repo = _repo()
        repo.get_by_id.return_value = current
        repo.get_by_name.return_value = by_name
        return UpdateExchangeService(repo), repo

    def test_not_found_returns_404(self):
        svc, repo = self._make(None)

        _assert_failed(svc.update(99, name="X"), "EXCHANGE_NOT_FOUND", 404, repo)

    def test_rename_to_a_name_of_another_exchange_is_409(self):
        current = Exchange(id=1, name="Binance", type="crypto_exchange")
        other = Exchange(id=2, name="Bybit", type="crypto_exchange")
        svc, repo = self._make(current, by_name=other)

        _assert_failed(svc.update(1, name="Bybit"), "EXCHANGE_NAME_EXISTS", 409, repo)
        repo.update.assert_not_called()

    def test_keeping_its_own_name_is_allowed(self):
        current = Exchange(id=1, name="Binance", type="crypto_exchange")
        svc, repo = self._make(current, by_name=current)

        result = svc.update(1, name="Binance", is_active=False)

        assert result.success is True
        assert result.data.is_active is False
        repo.commit.assert_called_once()

    def test_invalid_type_is_422(self):
        svc, repo = self._make(Exchange(id=1, name="Binance", type="crypto_exchange"))

        _assert_failed(svc.update(1, type="bank"), "EXCHANGE_INVALID_TYPE", 422, repo)
        repo.update.assert_not_called()

    def test_only_sent_fields_change(self):
        svc, repo = self._make(Exchange(id=1, name="TradingView", type="crypto_exchange"))

        result = svc.update(1, type="data_vendor")

        assert (result.data.name, result.data.type, result.data.is_active) == ("TradingView", "data_vendor", True)
        repo.get_by_name.assert_not_called()
        repo.commit.assert_called_once()


class TestListExchangesService:

    def test_passes_active_filter_to_repo(self):
        repo = _repo()
        repo.list_all.return_value = []

        result = ListExchangesService(repo).list(is_active=True)

        assert result.success is True
        repo.list_all.assert_called_once_with(is_active=True)


# ======================================================================
# Símbolos
# ======================================================================

class TestCreateSymbolService:

    def _make(self, exchange: Exchange | None, existing: Symbol | None = None):
        symbol_repo = _repo()
        symbol_repo.get_by_exchange_and_symbol.return_value = existing
        exchange_repo = MagicMock()
        exchange_repo.get_by_id.return_value = exchange
        return CreateSymbolService(symbol_repo=symbol_repo, exchange_repo=exchange_repo), symbol_repo

    def test_creates_perpetual_symbol_and_commits(self):
        svc, repo = self._make(Exchange(id=1, name="Binance", type="crypto_exchange"))

        result = svc.create(
            exchange_id=1, symbol="XAU/USDT:USDT", asset_class="metal",
            base_asset="XAU", quote_asset="USDT", tick_size=Decimal("0.01"), lot_size=Decimal("0.001"),
        )

        assert result.success is True
        assert result.data.symbol == "XAU/USDT:USDT"
        assert result.data.tick_size == Decimal("0.01")
        assert result.data.is_active is True
        repo.commit.assert_called_once()

    def test_exchange_must_exist(self):
        svc, repo = self._make(None)

        _assert_failed(svc.create(exchange_id=9, symbol="BTC/USDT", asset_class="crypto"), "EXCHANGE_NOT_FOUND", 404, repo)

    def test_invalid_asset_class_is_422(self):
        svc, repo = self._make(Exchange(id=1, name="Binance", type="crypto_exchange"))

        _assert_failed(svc.create(exchange_id=1, symbol="BTC/USDT", asset_class="bond"), "SYMBOL_INVALID_ASSET_CLASS", 422, repo)

    def test_same_symbol_in_same_exchange_is_409(self):
        existing = Symbol(id=3, exchange_id=1, symbol="BTC/USDT", asset_class="crypto")
        svc, repo = self._make(Exchange(id=1, name="Binance", type="crypto_exchange"), existing=existing)

        _assert_failed(svc.create(exchange_id=1, symbol="BTC/USDT", asset_class="crypto"), "SYMBOL_ALREADY_EXISTS", 409, repo)
        repo.create.assert_not_called()


class TestUpdateSymbolService:

    def _symbol(self) -> Symbol:
        return Symbol(
            id=5, exchange_id=1, symbol="XAU/USDT:USDT", asset_class="commodity",
            base_asset="XAU", quote_asset="USDT", tick_size=Decimal("0.01"),
        )

    def test_not_found_is_404(self):
        repo = _repo()
        repo.get_by_id.return_value = None

        _assert_failed(UpdateSymbolService(repo).update(5, is_active=False), "SYMBOL_NOT_FOUND", 404, repo)

    def test_invalid_asset_class_is_422(self):
        repo = _repo()
        repo.get_by_id.return_value = self._symbol()

        _assert_failed(UpdateSymbolService(repo).update(5, asset_class="bond"), "SYMBOL_INVALID_ASSET_CLASS", 422, repo)
        repo.update.assert_not_called()

    def test_partial_update_keeps_other_fields(self):
        repo = _repo()
        repo.get_by_id.return_value = self._symbol()

        result = UpdateSymbolService(repo).update(5, asset_class="metal", is_active=False)

        assert result.success is True
        assert (result.data.asset_class, result.data.is_active) == ("metal", False)
        assert (result.data.base_asset, result.data.tick_size) == ("XAU", Decimal("0.01"))
        repo.commit.assert_called_once()


class TestListSymbolsService:

    def test_passes_filters_to_repo(self):
        repo = _repo()
        repo.list_all.return_value = []

        ListSymbolsService(repo).list(exchange_id=1, asset_class="metal", is_active=True)

        repo.list_all.assert_called_once_with(exchange_id=1, asset_class="metal", is_active=True)


# ======================================================================
# Timeframes
# ======================================================================

class TestCreateTimeframeService:

    def test_creates_timeframe_and_commits(self):
        repo = _repo()
        repo.get_by_code.return_value = None

        result = CreateTimeframeService(repo).create(code="2h", seconds=7200)

        assert result.success is True
        assert (result.data.code, result.data.seconds) == ("2h", 7200)
        repo.commit.assert_called_once()

    def test_zero_or_negative_seconds_is_422(self):
        for seconds in (0, -60):
            repo = _repo()
            _assert_failed(CreateTimeframeService(repo).create(code="x", seconds=seconds), "TIMEFRAME_INVALID_SECONDS", 422, repo)
            repo.get_by_code.assert_not_called()

    def test_duplicate_code_is_409(self):
        repo = _repo()
        repo.get_by_code.return_value = Timeframe(id=1, code="1h", seconds=3600)

        _assert_failed(CreateTimeframeService(repo).create(code="1h", seconds=3600), "TIMEFRAME_CODE_EXISTS", 409, repo)
        repo.create.assert_not_called()


class TestListTimeframesService:

    def test_returns_repo_list(self):
        repo = _repo()
        repo.list_all.return_value = [Timeframe(id=1, code="1h", seconds=3600)]

        result = ListTimeframesService(repo).list()

        assert [tf.code for tf in result.data] == ["1h"]
