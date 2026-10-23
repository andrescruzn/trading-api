# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/domain/mail_template.py
#
# PROPÓSITO:
# - Definir el catálogo de templates de correo soportados por el sistema.
#
# POR QUÉ:
# - Evitamos "strings mágicos" dispersos (welcome, otp, etc.).
# - Facilita escalar a nuevos correos con consistencia.
# ======================================================================

from dataclasses import dataclass


# ----------------------------------------------------------------------
# Value Object: MailTemplate
# ----------------------------------------------------------------------
# - Representa un template disponible para renderizar un correo.
# - No sabe nada de SMTP, FastAPI ni filesystem.
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class MailTemplate:
    """
    Template de correo (catálogo).
    """
    code: str          # Identificador estable (ej: "welcome", "otp")
    subject: str       # Asunto por defecto asociado al template
    filename: str      # Archivo HTML dentro de app/modules/mailer/templates/


# ----------------------------------------------------------------------
# Catálogo centralizado de templates
# ----------------------------------------------------------------------
WELCOME_TEMPLATE = MailTemplate(
    code="welcome",
    subject="Tu cuenta en Trading App está lista",
    filename="welcome.html",
)

OTP_TEMPLATE = MailTemplate(
    code="otp",
    subject="Tu código OTP de acceso",
    filename="otp.html",
)

ALERT_TEMPLATE = MailTemplate(
    code="alert",
    subject="Alerta de Trading App",
    filename="alert.html",
)
# Avisos del fondo común (depósitos, liquidaciones, retiros); el asunto se
# reemplaza por el título del aviso.
FUND_NOTICE_TEMPLATE = MailTemplate(
    code="fund_notice",
    subject="Novedad de tu inversión en Trading App",
    filename="fund_notice.html",
)
