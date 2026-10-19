# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/providers/order_provider.py
#
# Factory que centraliza la creación de todos los servicios del Módulo 8.
#
# PATRÓN:
# - Instancia repos propios (Order, Fill, Position).
# - Borrow de repos de otros módulos necesarios para los servicios:
#     M7 → BotRepository (validar bot, obtener mode/symbol)
#          SignalRepository (validar la señal vinculada a la orden)
#     M2 → CandleRepository (PaperExecutor necesita el último close)
#          SymbolRepository (CreateOrderService guarda symbol en meta)
#          ExchangeRepository (LiveExecutor necesita el exchange del account)
#     M4 → AccountRepository (propiedad y credenciales del LiveExecutor)
#          AccountBalanceRepository (RiskGate: capital para el drawdown)
# - Construye PaperExecutor y LiveExecutor con sus dependencias.
# - Expone métodos que retornan servicios listos para usar.
#
# USO EN ROUTES:
#     factory = OrderServiceFactory(session=db)
#     result  = factory.create_order().create(bot_id=1, side="buy", ...)
#     result  = factory.list_orders().list(bot_id=1)
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings

from app.common.security.credentials_cipher import CredentialsCipher

# Repos propios del módulo
from app.modules.orders.infrastructure import (
    SqlAlchemyFillRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyPositionRepository,
)

# Servicios propios
from app.modules.orders.services.fills.list_fills_service import ListFillsService
from app.modules.orders.services.orders.create_order_service import CreateOrderService
from app.modules.orders.services.orders.get_order_service import GetOrderService
from app.modules.orders.services.orders.list_orders_service import ListOrdersService
from app.modules.orders.services.positions.list_positions_service import ListPositionsService
from app.modules.orders.services.risk.risk_gate_service import RiskGateService
from app.modules.orders.services.execution import (
    ExecuteSignalService,
    NativeStopService,
    ProtectPositionsService,
    ReconcileOrdersService,
)

# Ejecutores (patrón Strategy)
from app.modules.orders.execution.paper_executor import PaperExecutor
from app.modules.orders.execution.live_executor import LiveExecutor

# Repos borrowed de otros módulos
from app.modules.bots.infrastructure import SqlAlchemyBotRepository, SqlAlchemySignalRepository
from app.modules.market.infrastructure import (
    SqlAlchemyCandleRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyExchangeRepository,
)
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountBalanceRepository,
    SqlAlchemyAccountRepository,
)
from app.modules.alerts.providers.alert_provider import build_evaluate_alerts_service


class OrderServiceFactory:
    """
    Factory para todos los servicios del módulo Orders.

    Todos los repos se crean una sola vez por request (misma sesión).
    Los ejecutores también se crean una vez — son stateless.
    """

    def __init__(self, session: Session):
        self._session = session

        # ------------------------------------------------------------------
        # Repos propios
        # ------------------------------------------------------------------
        self._order_repo = SqlAlchemyOrderRepository(session)
        self._fill_repo = SqlAlchemyFillRepository(session)
        self._position_repo = SqlAlchemyPositionRepository(session)

        # ------------------------------------------------------------------
        # Repos borrowed de otros módulos
        # ------------------------------------------------------------------
        self._bot_repo = SqlAlchemyBotRepository(session)
        self._signal_repo = SqlAlchemySignalRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._exchange_repo = SqlAlchemyExchangeRepository(session)
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)

        # ------------------------------------------------------------------
        # Cipher para descifrar credenciales API (LiveExecutor)
        # ------------------------------------------------------------------
        self._cipher = CredentialsCipher.from_settings()

        # ------------------------------------------------------------------
        # Ejecutores (patrón Strategy) — stateless, se pueden reutilizar
        # ------------------------------------------------------------------
        self._paper_executor = PaperExecutor(candle_repo=self._candle_repo)
        self._live_executor = LiveExecutor(
            account_repo=self._account_repo,
            exchange_repo=self._exchange_repo,
            cipher=self._cipher,
        )

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def list_orders(self) -> ListOrdersService:
        return ListOrdersService(
            repo=self._order_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )

    def get_order(self) -> GetOrderService:
        return GetOrderService(
            repo=self._order_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )

    def risk_gate(self) -> RiskGateService:
        return RiskGateService(
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
            balance_repo=self._balance_repo,
            position_repo=self._position_repo,
        )

    def create_order(self) -> CreateOrderService:
        return CreateOrderService(
            order_repo=self._order_repo,
            fill_repo=self._fill_repo,
            position_repo=self._position_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
            signal_repo=self._signal_repo,
            symbol_repo=self._symbol_repo,
            candle_repo=self._candle_repo,
            risk_gate=self.risk_gate(),
            paper_executor=self._paper_executor,
            live_executor=self._live_executor,
            evaluate_alerts=build_evaluate_alerts_service(self._session),
            native_stop=self.native_stop(),
        )

    # ------------------------------------------------------------------
    # Ejecución de señales (modo approval / auto) y protección SL/TP
    # ------------------------------------------------------------------

    def native_stop(self) -> NativeStopService:
        return NativeStopService(
            order_repo=self._order_repo,
            position_repo=self._position_repo,
            symbol_repo=self._symbol_repo,
            live_executor=self._live_executor,
        )

    def reconcile_orders(self) -> ReconcileOrdersService:
        return ReconcileOrdersService(
            order_repo=self._order_repo,
            fill_repo=self._fill_repo,
            position_repo=self._position_repo,
            bot_repo=self._bot_repo,
            live_executor=self._live_executor,
            evaluate_alerts=build_evaluate_alerts_service(self._session),
        )

    def execute_signal(self) -> ExecuteSignalService:
        return ExecuteSignalService(
            signal_repo=self._signal_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
            candle_repo=self._candle_repo,
            position_repo=self._position_repo,
            create_order=self.create_order(),
            min_rr_ratio=settings.AGENT_MIN_RR_RATIO,
            native_stop=self.native_stop() if settings.ORDER_NATIVE_STOP_LOSS else None,
        )

    def protect_positions(self) -> ProtectPositionsService:
        return ProtectPositionsService(
            position_repo=self._position_repo,
            bot_repo=self._bot_repo,
            candle_repo=self._candle_repo,
            create_order=self.create_order(),
        )

    # ------------------------------------------------------------------
    # Fills
    # ------------------------------------------------------------------

    def list_fills(self) -> ListFillsService:
        return ListFillsService(
            fill_repo=self._fill_repo,
            order_repo=self._order_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def list_positions(self) -> ListPositionsService:
        return ListPositionsService(
            repo=self._position_repo,
            bot_repo=self._bot_repo,
            account_repo=self._account_repo,
        )


def get_order_factory(session: Session) -> OrderServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return OrderServiceFactory(session=session)
