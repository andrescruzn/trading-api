# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/providers/agent_provider.py
#
# Factory que centraliza la creación de todos los servicios del módulo Agent.
#
# PATRÓN:
# - Instancia una vez los repos al inicio.
# - Expone métodos que retornan servicios listos para usar.
# - Borrow de repos de otros módulos para AnalyzeService.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.agent.infrastructure import (
    SqlAlchemyMLModelRepository,
    SqlAlchemyModelRunRepository,
)
from app.modules.agent.llm import LLMClientFactory
from app.modules.agent.services.agent import AnalyzeService
from app.modules.agent.services.model_runs import (
    CreateModelRunService,
    FinishModelRunService,
    ListModelRunsService,
)
from app.modules.agent.services.models import (
    CreateModelService,
    GetModelService,
    ListModelsService,
    UpdateModelService,
)

# Repos de otros módulos (borrowing)
from app.modules.strategies.infrastructure import SqlAlchemyStrategyRepository
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAccountBalanceRepository,
)
from app.modules.features.infrastructure import SqlAlchemyCandleFeatureRepository
from app.modules.market.infrastructure import (
    SqlAlchemyCandleRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
)


class AgentServiceFactory:
    """
    Factory para todos los servicios del módulo Agent.

    Uso en routes:
        factory = AgentServiceFactory(session=db)
        result  = factory.analyze().analyze(...)
    """

    def __init__(self, session: Session):
        self._session = session

        # Repos propios del módulo
        self._model_repo = SqlAlchemyMLModelRepository(session)
        self._run_repo = SqlAlchemyModelRunRepository(session)

        # Repos tomados de otros módulos (borrowing)
        self._strategy_repo = SqlAlchemyStrategyRepository(session)
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)
        self._candle_feature_repo = SqlAlchemyCandleFeatureRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._timeframe_repo = SqlAlchemyTimeframeRepository(session)

    # ------------------------------------------------------------------
    # Agent
    # ------------------------------------------------------------------

    def analyze(self) -> AnalyzeService:
        """
        Crea el servicio AnalyzeService con todas sus dependencias.

        El LLMClient se crea en cada request para respetar posibles
        cambios en la configuración sin reiniciar el servidor.
        """
        llm_client = LLMClientFactory.create(settings)

        return AnalyzeService(
            strategy_repo=self._strategy_repo,
            account_repo=self._account_repo,
            balance_repo=self._balance_repo,
            candle_feature_repo=self._candle_feature_repo,
            candle_repo=self._candle_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
            llm_client=llm_client,
            min_rr_ratio=settings.AGENT_MIN_RR_RATIO,
            master_prompt=settings.AGENT_MASTER_PROMPT,
        )

    # ------------------------------------------------------------------
    # ML Models
    # ------------------------------------------------------------------

    def list_models(self) -> ListModelsService:
        return ListModelsService(repo=self._model_repo)

    def get_model(self) -> GetModelService:
        return GetModelService(repo=self._model_repo)

    def create_model(self) -> CreateModelService:
        return CreateModelService(repo=self._model_repo, session=self._session)

    def update_model(self) -> UpdateModelService:
        return UpdateModelService(repo=self._model_repo, session=self._session)

    # ------------------------------------------------------------------
    # Model Runs
    # ------------------------------------------------------------------

    def list_model_runs(self) -> ListModelRunsService:
        return ListModelRunsService(repo=self._run_repo)

    def create_model_run(self) -> CreateModelRunService:
        return CreateModelRunService(
            run_repo=self._run_repo,
            model_repo=self._model_repo,
            session=self._session,
        )

    def finish_model_run(self) -> FinishModelRunService:
        return FinishModelRunService(repo=self._run_repo, session=self._session)


def get_agent_factory(session: Session) -> AgentServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return AgentServiceFactory(session=session)
