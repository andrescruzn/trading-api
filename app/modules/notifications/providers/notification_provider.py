# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/providers/notification_provider.py
#
# - NotificationServiceFactory(session): servicios de la página
#   Administración → Notificaciones.
# - build_notification_settings_reader(session): lo que usan alerts,
#   users, bots y el scheduler para leer la configuración de los canales.
# - build_notification_mailer(): el MailerService si hay SMTP en .env, o
#   None (los avisos por correo no salen).
# ======================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.notifications.domain import NotificationSettingsReader
from app.modules.notifications.infrastructure import (
    HttpTelegramGateway,
    SqlAlchemyNotificationSettingsRepository,
)
from app.modules.notifications.services.settings import (
    GetNotificationSettingsService,
    SendEmailTestService,
    SendTelegramTestService,
    UpdateEmailSettingsService,
    UpdateTelegramSettingsService,
)
from app.modules.users.infrastructure import SqlAlchemyUserRepository

if TYPE_CHECKING:
    from app.modules.mailer.services.mailer_service import MailerService


def build_notification_settings_reader(session: Session) -> NotificationSettingsReader:
    return SqlAlchemyNotificationSettingsRepository(session)


def build_notification_mailer() -> "MailerService | None":
    from app.modules.mailer.providers.mailer_provider import build_mailer

    return build_mailer(settings) if settings.SMTP_HOST else None


class NotificationServiceFactory:

    def __init__(self, session: Session):
        self._session = session
        self._repo = SqlAlchemyNotificationSettingsRepository(session)
        self._gateway = HttpTelegramGateway()

    def get_settings(self) -> GetNotificationSettingsService:
        return GetNotificationSettingsService(
            reader=self._repo, smtp_configured=bool(settings.SMTP_HOST)
        )

    def update_telegram(self) -> UpdateTelegramSettingsService:
        return UpdateTelegramSettingsService(repo=self._repo, gateway=self._gateway)

    def update_email(self) -> UpdateEmailSettingsService:
        return UpdateEmailSettingsService(repo=self._repo)

    def send_telegram_test(self) -> SendTelegramTestService:
        return SendTelegramTestService(
            reader=self._repo,
            user_repo=SqlAlchemyUserRepository(self._session),
            gateway=self._gateway,
        )

    def send_email_test(self) -> SendEmailTestService:
        return SendEmailTestService(
            user_repo=SqlAlchemyUserRepository(self._session),
            mailer=build_notification_mailer(),
        )
