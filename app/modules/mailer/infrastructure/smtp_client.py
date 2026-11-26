# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/infrastructure/smtp_client.py
#
# PROPÓSITO:
# - Implementación concreta de MailClient usando SMTP.
#
# POR QUÉ:
# - Permite enviar correos desde Hostinger (smtp.hostinger.com).
# - El service NO debe conocer smtplib ni SSL.
#
# PATRÓN:
# - Adapter (adapta SMTP a nuestro contrato MailClient)
# ======================================================================

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.common.config.settings import Settings
from app.modules.mailer.domain.mail_contracts import MailClient, MailMessage


class SmtpMailClient(MailClient):
    """
    Cliente SMTP parametrizado por Settings.

    Regla:
    - Si falla el envío, levanta excepción.
    - El service captura y convierte a ServiceResult.fail.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, message: MailMessage) -> None:
        """
        Envío SMTP:
        - SSL (465) o STARTTLS (587).
        - Construimos EmailMessage con HTML + opcional texto plano.
        """

        # --------------------------------------------------------------
        # 1) Construcción del mensaje MIME
        # --------------------------------------------------------------
        email_msg = EmailMessage()
        email_msg["From"] = f"{self._settings.SMTP_FROM_NAME} <{self._settings.SMTP_FROM_EMAIL}>"
        email_msg["To"] = message.to_email
        email_msg["Subject"] = message.subject

        # --------------------------------------------------------------
        # 2) Body: texto plano opcional + HTML como alternativa
        # --------------------------------------------------------------
        if message.text_body:
            email_msg.set_content(message.text_body)

        email_msg.add_alternative(message.html_body, subtype="html")

        # --------------------------------------------------------------
        # 3) Conexión SMTP según modo (SSL vs STARTTLS)
        # --------------------------------------------------------------
        if self._settings.SMTP_USE_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                host=self._settings.SMTP_HOST,
                port=self._settings.SMTP_PORT,
                context=context,
                timeout=20,
            ) as server:
                server.login(self._settings.SMTP_USERNAME, self._settings.SMTP_PASSWORD)
                server.send_message(email_msg)
            return

        # --------------------------------------------------------------
        # 4) STARTTLS (si decides usar puerto 587)
        # --------------------------------------------------------------
        with smtplib.SMTP(
            host=self._settings.SMTP_HOST,
            port=self._settings.SMTP_PORT,
            timeout=20,
        ) as server:
            server.ehlo()

            if self._settings.SMTP_USE_STARTTLS:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

            server.login(self._settings.SMTP_USERNAME, self._settings.SMTP_PASSWORD)
            server.send_message(email_msg)