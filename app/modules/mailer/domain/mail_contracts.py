# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/domain/mail_contracts.py
#
# PROPÓSITO:
# - Definir contratos (puertos) del módulo Mailer.
#
# POR QUÉ:
# - Hexagonal: services dependen de contratos, no de implementaciones.
# - Permite reemplazar SMTP por SendGrid/Mailgun sin romper services.
#
# PATRÓN:
# - Ports & Adapters (Hexagonal)
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Dict, Any, Optional


# ----------------------------------------------------------------------
# Entidad simple: MailMessage (dominio)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class MailMessage:
    """
    Mensaje de correo en forma de dominio (sin transporte).
    """
    to_email: str
    subject: str
    html_body: str
    text_body: Optional[str] = None


# ----------------------------------------------------------------------
# Contrato: MailClient
# ----------------------------------------------------------------------
class MailClient(Protocol):
    """
    Puerto de salida: envío real del correo.

    Implementaciones típicas:
    - SMTP (Hostinger/Gmail/Outlook)
    - API providers (SendGrid, SES, Mailgun)
    """

    def send(self, message: MailMessage) -> None:
        """
        Envía un correo. Si falla, debe lanzar excepción
        para que el service traduzca a ServiceResult.fail.
        """
        raise NotImplementedError


# ----------------------------------------------------------------------
# Contrato: TemplateRenderer
# ----------------------------------------------------------------------
class TemplateRenderer(Protocol):
    """
    Puerto de salida: renderizado de templates.

    Implementaciones típicas:
    - Jinja2 filesystem
    - Plantillas desde DB
    """

    def render(self, template_filename: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un HTML a partir del filename y el contexto.
        """
        raise NotImplementedError