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
# ENVÍO EN SEGUNDO PLANO:
# - send_by_template_in_background() encola el envío y retorna de una vez:
#   el request no espera al SMTP. Reintenta y, si igual falla, lo deja en
#   el log (sin el contenido del correo ni la dirección completa).
#
# PATRONES:
# - Application Service Pattern (orquesta puertos + dominio)
# - Ports & Adapters (depende de contratos, no de infraestructura)
# ======================================================================

from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional

from app.common.contracts.service_result import ServiceResult
from app.common.utils import run_in_background
from app.common.utils.input_cleaner import clean_email, clean_str
from app.common.config.settings import Settings

from app.modules.mailer.domain.mail_contracts import MailClient, TemplateRenderer, MailMessage
from app.modules.mailer.domain.mail_template import MailTemplate

logger = logging.getLogger(__name__)

# Esperas entre reintentos del envío en segundo plano (segundos):
# 3 intentos en total.
_BACKGROUND_RETRY_DELAYS: tuple[int, ...] = (2, 10)


def _mask_email(email: str) -> str:
    """`ana@correo.com` → `a***@correo.com` (para logs)."""
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


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
                code="MAIL_SEND_FAILED",
                http_status=502,
                meta={"detail": str(exc), "template": template.code},
            )

    def send_by_template_in_background(
        self,
        *,
        to_email: str,
        template: MailTemplate,
        context: Dict[str, Any],
        subject_override: Optional[str] = None,
        text_body: Optional[str] = None,
    ) -> None:
        """
        Encola el envío (mismos parámetros que send_by_template) y retorna.

        - No informa el resultado: quien llama no puede depender de él.
        - Reintenta según _BACKGROUND_RETRY_DELAYS; el fallo final va al log.
        """
        run_in_background(
            self._send_with_retries,
            to_email=to_email,
            template=template,
            context=context,
            subject_override=subject_override,
            text_body=text_body,
        )

    def _send_with_retries(self, *, to_email: str, template: MailTemplate, **kwargs: Any) -> None:
        """Envía con reintentos; corre en el pool de segundo plano."""
        attempts = len(_BACKGROUND_RETRY_DELAYS) + 1

        for attempt in range(1, attempts + 1):
            result = self.send_by_template(to_email=to_email, template=template, **kwargs)
            if result.success:
                return

            detail = result.error.meta.get("detail") if result.error and result.error.meta else None
            if attempt < attempts:
                logger.warning(
                    "Mail send failed (attempt %s/%s, template=%s, to=%s): %s",
                    attempt, attempts, template.code, _mask_email(to_email), detail,
                )
                time.sleep(_BACKGROUND_RETRY_DELAYS[attempt - 1])
            else:
                logger.error(
                    "Mail send failed after %s attempts (template=%s, to=%s): %s",
                    attempts, template.code, _mask_email(to_email), detail,
                )