# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/providers/mailer_provider.py
#
# PROPÓSITO:
# - Centralizar la construcción (DI manual) de MailerService.
#
# POR QUÉ:
# - Evita instanciar infraestructura (SMTP/Jinja) dentro de endpoints.
# - Mantiene users/auth limpio: REST no conoce smtplib ni jinja2.
# - Facilita swap: SMTP -> SendGrid, Jinja -> DB templates, etc.
#
# PATRÓN:
# - Composition Root (manual DI)
# ======================================================================

from __future__ import annotations

from app.common.config.settings import Settings
from app.modules.mailer.services import MailerService
from app.modules.mailer.infrastructure.smtp_client import SmtpMailClient
from app.modules.mailer.infrastructure.template_renderer import JinjaTemplateRenderer


def build_mailer(settings: Settings) -> MailerService:
    """
    Factory que arma MailerService con adaptadores concretos.

    Retorna:
    - MailerService listo para usarse por cualquier caso de uso (OTP, welcome, etc.)
    """

    # --------------------------------------------------------------
    # 1) Adaptador de envío real (SMTP)
    # --------------------------------------------------------------
    mail_client = SmtpMailClient(settings=settings)

    # --------------------------------------------------------------
    # 2) Adaptador de render HTML (Jinja2)
    # --------------------------------------------------------------
    template_renderer = JinjaTemplateRenderer()

    # --------------------------------------------------------------
    # 3) Application Service: orquesta render + envío
    # --------------------------------------------------------------
    return MailerService(
        settings=settings,
        mail_client=mail_client,
        template_renderer=template_renderer,
    )