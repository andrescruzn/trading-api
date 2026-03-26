# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/providers/bot_provider.py
#
# Factory que centraliza la creación de todos los servicios del módulo Bots.
#
# PATRÓN:
# - Instancia repos propios (BotRepository, SignalRepository).
# - Borrow de repos de otros módulos para construir el AnalyzeService.
# - El AnalyzeService (M6) se construye aquí y se inyecta en
#   GenerateSignalService, que no conoce sus dependencias internas.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.agent.llm import LLMClientFactory
from app.modules.agent.services.agent import AnalyzeService

# Repos propios
from app.modules.bots.infrastructure import (
    SqlAlchemyBotRepository,
    SqlAlchemySignalRepository,
)

# Servicios propios
from app.modules.bots.services.bots import (
    CreateBotService,
    GetBotService,
    ListBotsService,
    UpdateBotService,
    UpdateBotStatusService,
)
from app.modules.bots.services.signals import GenerateSignalService, ListSignalsService

# Repos tomados de otros módulos (borrowing)
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
from app.modules.alerts.providers.alert_provider import build_evaluate_alerts_service


class BotServiceFactory:
    """
    Factory para todos los servicios del módulo Bots.

    Uso en routes:
        factory = BotServiceFactory(session=db)
        result  = factory.list_bots().list(account_id=1)
        result  = factory.generate_signal().generate(bot_id=5)
    """

    def __init__(self, session: Session):
        self._session = session

        # Repos propios del módulo
        self._bot_repo = SqlAlchemyBotRepository(session)
        self._signal_repo = SqlAlchemySignalRepository(session)

        # Repos de otros módulos (borrowing) — necesarios para AnalyzeService
        self._strategy_repo = SqlAlchemyStrategyRepository(session)
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)
        self._candle_feature_repo = SqlAlchemyCandleFeatureRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._timeframe_repo = SqlAlchemyTimeframeRepository(session)

    # ------------------------------------------------------------------
    # Helper privado: construye AnalyzeService con todas sus dependencias
    # ------------------------------------------------------------------

    def _build_analyze_service(self) -> AnalyzeService:
        """
        Construye el AnalyzeService del Agente (M6) con todas sus dependencias.

        El LLMClient se crea en cada llamada para respetar posibles
        cambios de configuración sin reiniciar el servidor.
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
    # Bots
    # ------------------------------------------------------------------

    def list_bots(self) -> ListBotsService:
        return ListBotsService(repo=self._bot_repo)

    def get_bot(self) -> GetBotService:
        return GetBotService(repo=self._bot_repo)

    def create_bot(self) -> CreateBotService:
        return CreateBotService(repo=self._bot_repo, session=self._session)

    def update_bot(self) -> UpdateBotService:
        return UpdateBotService(repo=self._bot_repo, session=self._session)

    def update_bot_status(self) -> UpdateBotStatusService:
        return UpdateBotStatusService(repo=self._bot_repo, session=self._session)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def list_signals(self) -> ListSignalsService:
        return ListSignalsService(repo=self._signal_repo)

    def generate_signal(self) -> GenerateSignalService:
        return GenerateSignalService(
            bot_repo=self._bot_repo,
            signal_repo=self._signal_repo,
            analyze_service=self._build_analyze_service(),
            session=self._session,
            evaluate_alerts=build_evaluate_alerts_service(self._session),
        )


def get_bot_factory(session: Session) -> BotServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return BotServiceFactory(session=session)
