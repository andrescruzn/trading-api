# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/providers/bot_provider.py
#
# Factory que centraliza la creación de todos los servicios del módulo Bots.
#
# PATRÓN:
# - Instancia repos propios (BotRepository, SignalRepository,
#   SignalSubscriptionRepository).
# - Borrow de repos de otros módulos para construir el AnalyzeService.
# - El AnalyzeService (M6) se construye aquí y se inyecta en
#   GenerateSignalService, que no conoce sus dependencias internas.
# - Igual con la descarga de velas (M2) y el cálculo de indicadores (M3)
#   que usa SyncBotMarketDataService.
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
    SqlAlchemySignalSubscriptionRepository,
)

# Servicios propios
from app.modules.bots.services.bots import (
    CreateBotService,
    GetBotService,
    ListBotsService,
    SyncBotMarketDataService,
    UpdateBotService,
    UpdateBotStatusService,
)
from app.modules.bots.services.signals import (
    GenerateSignalService,
    ListPendingSignalsService,
    ListSignalsService,
)
from app.modules.bots.services.subscriptions import (
    ListSharedBotsService,
    SubscribeToBotService,
    UnsubscribeFromBotService,
)

# Repos tomados de otros módulos (borrowing)
from app.modules.strategies.infrastructure import SqlAlchemyStrategyRepository
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAccountBalanceRepository,
)
from app.modules.features.infrastructure import (
    SqlAlchemyCandleFeatureRepository,
    SqlAlchemyFeatureSetRepository,
)
from app.modules.market.infrastructure import (
    SqlAlchemyCandleRepository,
    SqlAlchemyExchangeRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
)
from app.modules.features.services.calculations import CalculateFeaturesService
from app.modules.market.services.candles import FetchCandlesService
from app.modules.alerts.providers.alert_provider import build_evaluate_alerts_service
from app.modules.alerts.providers.telegram_provider import (
    build_shared_signal_notifier,
    build_signal_approval_notifier,
)
from app.modules.users.infrastructure import SqlAlchemyUserRepository


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
        self._subscription_repo = SqlAlchemySignalSubscriptionRepository(session)

        # Repos de otros módulos (borrowing) — necesarios para AnalyzeService
        self._strategy_repo = SqlAlchemyStrategyRepository(session)
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)
        self._candle_feature_repo = SqlAlchemyCandleFeatureRepository(session)
        self._feature_set_repo = SqlAlchemyFeatureSetRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._timeframe_repo = SqlAlchemyTimeframeRepository(session)
        self._exchange_repo = SqlAlchemyExchangeRepository(session)

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
            max_entry_atr_distance=settings.AGENT_MAX_ENTRY_ATR_DISTANCE,
            master_prompt=settings.AGENT_MASTER_PROMPT,
        )

    # ------------------------------------------------------------------
    # Bots
    # ------------------------------------------------------------------

    def list_bots(self) -> ListBotsService:
        return ListBotsService(repo=self._bot_repo, account_repo=self._account_repo)

    def get_bot(self) -> GetBotService:
        return GetBotService(repo=self._bot_repo, account_repo=self._account_repo)

    def create_bot(self) -> CreateBotService:
        return CreateBotService(
            repo=self._bot_repo,
            account_repo=self._account_repo,
            strategy_repo=self._strategy_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
            feature_set_repo=self._feature_set_repo,
        )

    def update_bot(self) -> UpdateBotService:
        return UpdateBotService(
            repo=self._bot_repo,
            account_repo=self._account_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
        )

    def update_bot_status(self) -> UpdateBotStatusService:
        return UpdateBotStatusService(repo=self._bot_repo, account_repo=self._account_repo)

    def sync_bot_market_data(self) -> SyncBotMarketDataService:
        return SyncBotMarketDataService(
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
            fetch_candles=FetchCandlesService(
                candle_repo=self._candle_repo,
                symbol_repo=self._symbol_repo,
                timeframe_repo=self._timeframe_repo,
                exchange_repo=self._exchange_repo,
            ),
            calculate_features=CalculateFeaturesService(
                candle_repo=self._candle_repo,
                feature_set_repo=self._feature_set_repo,
                candle_feature_repo=self._candle_feature_repo,
                symbol_repo=self._symbol_repo,
                timeframe_repo=self._timeframe_repo,
            ),
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def list_signals(self) -> ListSignalsService:
        return ListSignalsService(
            repo=self._signal_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )

    def list_pending_signals(self) -> ListPendingSignalsService:
        return ListPendingSignalsService(
            repo=self._signal_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )

    def generate_signal(self) -> GenerateSignalService:
        return GenerateSignalService(
            bot_repo=self._bot_repo,
            signal_repo=self._signal_repo,
            analyze_service=self._build_analyze_service(),
            account_repo=self._account_repo,
            evaluate_alerts=build_evaluate_alerts_service(self._session),
            notify_pending=build_signal_approval_notifier(self._session).notify,
            approval_ttl_minutes=settings.SIGNAL_APPROVAL_TTL_MINUTES,
            notify_subscribers=build_shared_signal_notifier(self._session).notify,
        )

    # ------------------------------------------------------------------
    # Señales compartidas (suscripciones)
    # ------------------------------------------------------------------

    def list_shared_bots(self) -> ListSharedBotsService:
        return ListSharedBotsService(
            bot_repo=self._bot_repo,
            subscription_repo=self._subscription_repo,
            account_repo=self._account_repo,
            strategy_repo=self._strategy_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
        )

    def subscribe_to_bot(self) -> SubscribeToBotService:
        return SubscribeToBotService(
            bot_repo=self._bot_repo,
            subscription_repo=self._subscription_repo,
            account_repo=self._account_repo,
            user_repo=SqlAlchemyUserRepository(self._session),
        )

    def unsubscribe_from_bot(self) -> UnsubscribeFromBotService:
        return UnsubscribeFromBotService(
            bot_repo=self._bot_repo,
            subscription_repo=self._subscription_repo,
        )


def get_bot_factory(session: Session) -> BotServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return BotServiceFactory(session=session)
