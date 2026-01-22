# -*- coding: utf-8 -*-

# ======================================================================
# app/common/config/__init__.py
#
# Barrel exports + singleton Settings.
# ======================================================================

from .settings import Settings

# ----------------------------------------------------------------------
# Singleton del sistema:
# - Un solo objeto Settings para todo el runtime
# - Evita recrear Settings por request
# ----------------------------------------------------------------------
settings = Settings()

__all__ = ["settings", "Settings"]