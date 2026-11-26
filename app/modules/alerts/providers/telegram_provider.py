# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/providers/telegram_provider.py
#
# Wiring de los avisos de señales (Telegram y correo) y del bot:
# - build_signal_approval_notifier(session): señal por aprobar al dueño
#   (hook de GenerateSignalService, lo usa BotServiceFactory).
# - build_shared_signal_notifier(session): señales de un agente compartido
#   a sus suscriptores (hook de GenerateSignalService).
# - build_telegram_update_service(session): procesa mensajes y botones
#   (webhook y polling); None si Telegram no está activo.
#
# La configuración de los canales sale de la BD (módulo notifications).
#
# NOTA:
# - No se exporta en providers/__init__.py y los providers de orders y
#   users se importan dentro de la función: orders → alerts (hooks de
#   alertas) importa este paquete, y un import en el módulo crearía un ciclo.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.accounts.infrastructure import SqlAlchemyAccountRepository
from app.modules.alerts.channels.telegram_replier import TelegramReplier
from app.modules.alerts.services.telegram import (
    SharedSignalNotifier,
    SignalApprovalNotifier,
    TelegramUpdateService,
)
from app.modules.bots.infrastructure.signal_subscription_repository_impl import (
    SqlAlchemySignalSubscriptionRepository,
)
from app.modules.notifications.providers import (
    build_notification_mailer,
    build_notification_settings_reader,
)
from app.modules.market.infrastructure import (
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
)
from app.modules.strategies.infrastructure import SqlAlchemyStrategyRepository
from app.modules.users.infrastructure import SqlAlchemyUserRepository


def build_signal_approval_notifier(session: Session) -> SignalApprovalNotifier:
    return SignalApprovalNotifier(
        account_repo=SqlAlchemyAccountRepository(session),
        user_repo=SqlAlchemyUserRepository(session),
        symbol_repo=SqlAlchemySymbolRepository(session),
        timeframe_repo=SqlAlchemyTimeframeRepository(session),
        settings=settings,
        notification_settings=build_notification_settings_reader(session),
        mailer=build_notification_mailer(),
    )


def build_shared_signal_notifier(session: Session) -> SharedSignalNotifier:
    return SharedSignalNotifier(
        subscription_repo=SqlAlchemySignalSubscriptionRepository(session),
        account_repo=SqlAlchemyAccountRepository(session),
        user_repo=SqlAlchemyUserRepository(session),
        symbol_repo=SqlAlchemySymbolRepository(session),
        timeframe_repo=SqlAlchemyTimeframeRepository(session),
        strategy_repo=SqlAlchemyStrategyRepository(session),
        notification_settings=build_notification_settings_reader(session),
        mailer=build_notification_mailer(),
    )


def build_telegram_update_service(session: Session) -> TelegramUpdateService | None:
    """None si Telegram no está activo en Notificaciones (no hay a quién responder)."""
    token = build_notification_settings_reader(session).get().telegram_token
    if not token:
        return None

    from app.modules.orders.providers import OrderServiceFactory
    from app.modules.users.providers import AuthServiceFactory

    orders = OrderServiceFactory(session=session)

    def decide(action: str, signal_id: int, user_id: int):
        service = orders.execute_signal()
        if action == "approve":
            return service.execute(
                signal_id, owner_id=user_id, decided_by_user_id=user_id, channel="telegram"
            )
        return service.reject(
            signal_id, owner_id=user_id, decided_by_user_id=user_id, channel="telegram"
        )

    return TelegramUpdateService(
        user_repo=SqlAlchemyUserRepository(session),
        link_service=AuthServiceFactory(session=session).telegram_link(),
        decide=decide,
        replier=TelegramReplier(token),
    )
