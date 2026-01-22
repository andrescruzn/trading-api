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
    subject="Bienvenido a Trading AI",
    filename="welcome.html",
)

OTP_TEMPLATE = MailTemplate(
    code="otp",
    subject="Tu código OTP de acceso",
    filename="otp.html",
)