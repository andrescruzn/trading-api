# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/services/mailer_service.py
#
# PROPÓSITO:
# - Caso de uso genérico: enviar correos basados en templates.
#
# QUÉ RESUELVE:
# - Welcome, OTP, recuperación, alertas, etc.
# - Unifica rendering + envío en un solo servicio reutilizable.
#
# PATRONES:
# - Application Service Pattern (orquesta puertos + dominio)
# - Ports & Adapters (depende de contratos, no de infraestructura)
# ======================================================================

from __future__ import annotations

from typing import Dict, Any, Optional

from app.common.contracts.service_result import ServiceResult
from app.common.utils.input_cleaner import clean_email, clean_str
from app.common.config.settings import Settings

from app.modules.mailer.domain.mail_contracts import MailClient, TemplateRenderer, MailMessage
from app.modules.mailer.domain.mail_template import MailTemplate


class MailerService:
    """
    Servicio de aplicación para envío de correos por template.

    Nota de arquitectura:
    - Este servicio NO retorna HTTP.
    - Retorna ServiceResult (ok/fail), consistente con tu estándar.
    """

    def __init__(
        self,
        settings: Settings,
        mail_client: MailClient,
        template_renderer: TemplateRenderer,
    ) -> None:
        self._settings = settings
        self._mail_client = mail_client
        self._template_renderer = template_renderer

    def send_by_template(
        self,
        *,
        to_email: str,
        template: MailTemplate,
        context: Dict[str, Any],
        subject_override: Optional[str] = None,
        text_body: Optional[str] = None,
    ) -> ServiceResult:
        """
        Envía correo renderizando un template.

        Parámetros:
        - to_email: destinatario
        - template: catálogo (WELCOME_TEMPLATE, OTP_TEMPLATE, etc.)
        - context: variables para el HTML (ej: full_name, otp_code)
        - subject_override: si un caso particular quiere asunto custom
        - text_body: fallback texto plano (opcional)
        """

        try:
            # ----------------------------------------------------------
            # 1) Sanitización de inputs (obligatoria según tu estándar)
            # ----------------------------------------------------------
            to_email_clean = clean_email(to_email)
            # subject puede incluir textos de negocio → limpiamos string.
            subject = clean_str(subject_override or template.subject)

            # ----------------------------------------------------------
            # 2) Render HTML (infra renderer)
            # ----------------------------------------------------------
            html = self._template_renderer.render(template.filename, context)

            # ----------------------------------------------------------
            # 3) Construcción del mensaje de dominio y envío
            # ----------------------------------------------------------
            msg = MailMessage(
                to_email=to_email_clean,
                subject=subject,
                html_body=html,
                text_body=text_body,
            )

            self._mail_client.send(msg)

            # ----------------------------------------------------------
            # 4) Respuesta cruda (dominio) sin payload HTTP
            # ----------------------------------------------------------
            return ServiceResult.ok(
                {
                    "to_email": to_email_clean,
                    "template": template.code,
                }
            )

        except Exception as exc:
            # ----------------------------------------------------------
            # 5) No aborts, no HTTP aquí. Solo fallo de servicio.
            # ----------------------------------------------------------
            return ServiceResult.fail(
                {
                    "error": "MAIL_SEND_FAILED",
                    "detail": str(exc),
                    "template": template.code,
                }
            )