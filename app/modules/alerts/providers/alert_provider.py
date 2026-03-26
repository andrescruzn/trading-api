# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/providers/alert_provider.py
#
# Factory para todos los servicios del módulo Alerts.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.alerts.infrastructure import (
    SqlAlchemyAlertRuleRepository,
    SqlAlchemyAlertEventRepository,
)
from app.modules.alerts.services.alert_rules import (
    CreateAlertRuleService,
    ListAlertRulesService,
    UpdateAlertRuleService,
)
from app.modules.alerts.services.alert_events import ListAlertEventsService
from app.modules.alerts.services.evaluation import EvaluateAlertsService, FireAlertService
from app.modules.mailer.providers.mailer_provider import build_mailer


class AlertServiceFactory:
    """
    Factory para todos los servicios del módulo Alerts.

    Instancia los repositorios propios y construye todos los servicios.
    El mailer se construye una sola vez por request.
    """

    def __init__(self, session: Session, user_email: str | None = None):
        self._session = session
        self._user_email = user_email

        self._rule_repo = SqlAlchemyAlertRuleRepository(session)
        self._event_repo = SqlAlchemyAlertEventRepository(session)

        # Mailer opcional — se usa solo si email está habilitado en la regla
        self._mailer = build_mailer(settings) if settings.SMTP_HOST else None

        self._fire_service = FireAlertService(
            event_repo=self._event_repo,
            session=session,
            settings=settings,
            mailer=self._mailer,
            user_email=user_email,
        )

    # ------------------------------------------------------------------
    # Alert Rules
    # ------------------------------------------------------------------

    def list_alert_rules(self) -> ListAlertRulesService:
        return ListAlertRulesService(repo=self._rule_repo)

    def create_alert_rule(self) -> CreateAlertRuleService:
        return CreateAlertRuleService(repo=self._rule_repo, session=self._session)

    def update_alert_rule(self) -> UpdateAlertRuleService:
        return UpdateAlertRuleService(repo=self._rule_repo, session=self._session)

    # ------------------------------------------------------------------
    # Alert Events
    # ------------------------------------------------------------------

    def list_alert_events(self) -> ListAlertEventsService:
        return ListAlertEventsService(repo=self._event_repo)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_alerts(self) -> EvaluateAlertsService:
        return EvaluateAlertsService(
            rule_repo=self._rule_repo,
            fire_service=self._fire_service,
        )

    def fire_alert(self) -> FireAlertService:
        return self._fire_service


def get_alert_factory(session: Session) -> AlertServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return AlertServiceFactory(session=session)


def build_evaluate_alerts_service(session: Session) -> EvaluateAlertsService:
    """
    Helper para los hooks de M7/M8.
    Construye el servicio sin user_email (no se usa para email en hooks internos).
    """
    factory = AlertServiceFactory(session=session)
    return factory.evaluate_alerts()
