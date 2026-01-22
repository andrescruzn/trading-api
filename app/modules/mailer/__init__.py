# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/__init__.py
#
# PROPÓSITO:
# - Barrel exports del módulo Mailer (imports limpios).
# ======================================================================

from app.modules.mailer.domain.mail_template import WELCOME_TEMPLATE, OTP_TEMPLATE
from app.modules.mailer.services.mailer_service import MailerService