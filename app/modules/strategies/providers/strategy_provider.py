# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/providers/strategy_provider.py
#
# Factory que centraliza la creación de todos los servicios del módulo
# Strategies. Sigue el mismo patrón que AccountServiceFactory.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.strategies.infrastructure import (
    SqlAlchemyStrategyRepository,
    SqlAlchemyDatasetRepository,
)
from app.modules.strategies.services.strategies import (
    ListStrategiesService,
    GetStrategyService,
    CreateStrategyService,
    UpdateStrategyService,
)
from app.modules.strategies.services.datasets import (
    ListDatasetsService,
    GetDatasetService,
    CreateDatasetService,
)
from app.modules.strategies.services.backtests import RunBacktestService

# Repos tomados de M2 (borrowing) para traer la historia del exchange
from app.modules.market.infrastructure import (
    SqlAlchemyExchangeRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
)
from app.modules.market.services.candles import FetchCandleHistoryService


class StrategyServiceFactory:
    """
    Factory para todos los servicios del módulo Strategies.

    Uso en routes:
        factory = StrategyServiceFactory(session=db)
        result = factory.list_strategies().list()
    """

    def __init__(self, session: Session):
        self._session = session
        self._strategy_repo = SqlAlchemyStrategyRepository(session)
        self._dataset_repo = SqlAlchemyDatasetRepository(session)

    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------

    def list_strategies(self) -> ListStrategiesService:
        return ListStrategiesService(repo=self._strategy_repo)

    def get_strategy(self) -> GetStrategyService:
        return GetStrategyService(repo=self._strategy_repo)

    def create_strategy(self) -> CreateStrategyService:
        return CreateStrategyService(repo=self._strategy_repo)

    def update_strategy(self) -> UpdateStrategyService:
        return UpdateStrategyService(repo=self._strategy_repo)

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------

    def list_datasets(self) -> ListDatasetsService:
        return ListDatasetsService(repo=self._dataset_repo)

    def get_dataset(self) -> GetDatasetService:
        return GetDatasetService(repo=self._dataset_repo)

    def create_dataset(self) -> CreateDatasetService:
        return CreateDatasetService(repo=self._dataset_repo)

    # ------------------------------------------------------------------
    # Backtesting
    # ------------------------------------------------------------------

    def run_backtest(self) -> RunBacktestService:
        return RunBacktestService(
            strategy_repo=self._strategy_repo,
            fetch_history=FetchCandleHistoryService(
                symbol_repo=SqlAlchemySymbolRepository(self._session),
                timeframe_repo=SqlAlchemyTimeframeRepository(self._session),
                exchange_repo=SqlAlchemyExchangeRepository(self._session),
            ),
        )
