# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/domain/__init__.py
# ======================================================================

from app.modules.mailer.domain.mail_template import MailTemplate, WELCOME_TEMPLATE, OTP_TEMPLATE
from app.modules.mailer.domain.mail_contracts import MailClient, TemplateRenderer, MailMessage