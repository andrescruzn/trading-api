# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/providers/__init__.py
#
# Barrel exports del módulo providers.
# ======================================================================

from app.modules.mailer.providers.mailer_provider import build_mailer

__all__ = ["build_mailer"]