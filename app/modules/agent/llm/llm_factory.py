# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/llm_factory.py
#
# Factory que arma el pool de servicios LLM según LLM_SERVICES en settings.
#
# - Cada nombre de LLM_SERVICES se busca en LLM_SERVICE_CATALOG.
# - Se omiten (con warning) los nombres desconocidos y los servicios sin
#   API key.
# - Cada servicio se construye con su cliente (SDK oficial) del catálogo.
# - Devuelve un RotatingLLMClient (round-robin + failover).
# ======================================================================

from __future__ import annotations

import logging

from app.common.config import settings as _settings
from app.modules.agent.llm.llm_client import LLMClient
from app.modules.agent.llm.llm_services import LLM_SERVICE_CATALOG, LLMServiceSpec
from app.modules.agent.llm.rotating_client import RotatingLLMClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """
    Factory para instanciar el pool de clientes LLM según la configuración.

    Uso:
        client = LLMClientFactory.create()
        response = client.complete(system_prompt, user_message)
    """

    @staticmethod
    def create(settings=None) -> LLMClient:
        """
        Crea el pool con los servicios configurados en settings.

        Args:
            settings: instancia de Settings (usa la global por defecto).
                      Inyectable en tests para usar distintas configs.

        Returns:
            RotatingLLMClient listo para usar. Si no hay servicios
            configurados, el pool falla en `complete` con LLMCallError.
        """
        cfg = settings or _settings
        services: list[tuple[str, LLMClient]] = []

        for spec in LLMClientFactory._configured_specs(cfg):
            services.append((
                spec.name,
                spec.client_cls(
                    api_key=getattr(cfg, spec.api_key_setting),
                    model=getattr(cfg, spec.model_setting),
                    temperature=cfg.LLM_TEMPERATURE,
                    max_tokens=cfg.LLM_MAX_TOKENS,
                    timeout=cfg.LLM_TIMEOUT_SECONDS,
                ),
            ))

        return RotatingLLMClient(services)

    @staticmethod
    def describe(settings=None) -> list[str]:
        """Nombres de los servicios que entrarían en el pool (para logs de arranque)."""
        cfg = settings or _settings
        return [spec.name for spec in LLMClientFactory._configured_specs(cfg, warn=True)]

    @staticmethod
    def _configured_specs(cfg, warn: bool = False) -> list[LLMServiceSpec]:
        specs: list[LLMServiceSpec] = []
        for name in cfg.LLM_SERVICES:
            spec = LLM_SERVICE_CATALOG.get(name)
            if spec is None:
                if warn:
                    logger.warning("[llm] servicio desconocido en LLM_SERVICES: '%s'", name)
                continue
            if not getattr(cfg, spec.api_key_setting, ""):
                if warn:
                    logger.warning("[llm] %s sin %s: se omite", name, spec.api_key_setting)
                continue
            specs.append(spec)
        return specs
