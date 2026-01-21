# -*- coding: utf-8 -*-

from .settings import Settings

# Singleton del sistema
settings = Settings()

__all__ = ["settings", "Settings"]