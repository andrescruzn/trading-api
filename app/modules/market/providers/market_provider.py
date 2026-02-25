# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/providers/market_provider.py
#
# Factory que centraliza la creación de todos los servicios de market data.
# Patrón: Factory + Dependency Injection (igual que AuthServiceFactory).
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.market.infrastructure import (
    SqlAlchemyExchangeRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
    SqlAlchemyCandleRepository,
)
from app.modules.market.services.exchanges import (
    ListExchangesService,
    CreateExchangeService,
    UpdateExchangeService,
)
from app.modules.market.services.symbols import (
    ListSymbolsService,
    CreateSymbolService,
    UpdateSymbolService,
)
from app.modules.market.services.timeframes import (
    ListTimeframesService,
    CreateTimeframeService,
)
from app.modules.market.services.candles import (
    ListCandlesService,
    IngestCandlesService,
    FetchCandlesService,
)


class MarketServiceFactory:
    """
    Factory para todos los servicios del módulo Market Data.

    Uso en routes:
        factory = MarketServiceFactory(session=db)
        result = factory.list_exchanges().list(is_active=True)
    """

    def __init__(self, session: Session):
        self._session = session

        # Repositorios compartidos entre servicios
        self._exchange_repo = SqlAlchemyExchangeRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._timeframe_repo = SqlAlchemyTimeframeRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)

    # ------------------------------------------------------------------
    # Exchanges
    # ------------------------------------------------------------------

    def list_exchanges(self) -> ListExchangesService:
        return ListExchangesService(repo=self._exchange_repo)

    def create_exchange(self) -> CreateExchangeService:
        return CreateExchangeService(repo=self._exchange_repo, session=self._session)

    def update_exchange(self) -> UpdateExchangeService:
        return UpdateExchangeService(repo=self._exchange_repo, session=self._session)

    # ------------------------------------------------------------------
    # Symbols
    # ------------------------------------------------------------------

    def list_symbols(self) -> ListSymbolsService:
        return ListSymbolsService(repo=self._symbol_repo)

    def create_symbol(self) -> CreateSymbolService:
        return CreateSymbolService(
            symbol_repo=self._symbol_repo,
            exchange_repo=self._exchange_repo,
            session=self._session,
        )

    def update_symbol(self) -> UpdateSymbolService:
        return UpdateSymbolService(repo=self._symbol_repo, session=self._session)

    # ------------------------------------------------------------------
    # Timeframes
    # ------------------------------------------------------------------

    def list_timeframes(self) -> ListTimeframesService:
        return ListTimeframesService(repo=self._timeframe_repo)

    def create_timeframe(self) -> CreateTimeframeService:
        return CreateTimeframeService(repo=self._timeframe_repo, session=self._session)

    # ------------------------------------------------------------------
    # Candles
    # ------------------------------------------------------------------

    def list_candles(self) -> ListCandlesService:
        return ListCandlesService(
            candle_repo=self._candle_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
        )

    def ingest_candles(self) -> IngestCandlesService:
        return IngestCandlesService(
            candle_repo=self._candle_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
            session=self._session,
        )

    def fetch_candles(self) -> FetchCandlesService:
        return FetchCandlesService(
            candle_repo=self._candle_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
            exchange_repo=self._exchange_repo,
            session=self._session,
        )


# ======================================================================
# Dependency para FastAPI
# ======================================================================

def get_market_factory(session: Session) -> MarketServiceFactory:
    return MarketServiceFactory(session=session)
