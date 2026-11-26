# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/providers/fund_notice_provider.py
#
# Wiring de los avisos del fondo común: build_fund_notifier(session) lo
# usa FundServiceFactory (import diferido, como los otros hooks de
# alertas). No se exporta en providers/__init__.py.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.alerts.infrastructure import SqlAlchemyAlertEventRepository
from app.modules.alerts.services.notifications.fund_notice_service import FundNoticeService
from app.modules.notifications.providers import (
    build_notification_mailer,
    build_notification_settings_reader,
)
from app.modules.users.infrastructure import SqlAlchemyUserRepository


def build_fund_notifier(session: Session) -> FundNoticeService:
    return FundNoticeService(
        event_repo=SqlAlchemyAlertEventRepository(session),
        user_repo=SqlAlchemyUserRepository(session),
        mailer=build_notification_mailer(),
        settings=settings,
        super_admin_role_id=settings.AUTH_SUPER_ADMIN_ROLE_ID,
        notification_settings=build_notification_settings_reader(session),
    )
