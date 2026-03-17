# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/llm_factory.py
#
# Factory que crea el cliente LLM correcto según LLM_PROVIDER en settings.
#
# MAPA DE PROVIDERS:
#   openai    → OpenAICompatibleClient (base_url=None)
#   xai       → OpenAICompatibleClient (base_url="https://api.x.ai/v1")
#   deepseek  → OpenAICompatibleClient (base_url="https://api.deepseek.com")
#   gemini    → OpenAICompatibleClient (base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
#   ollama    → OpenAICompatibleClient (base_url settings o "http://localhost:11434/v1")
#   anthropic → AnthropicLLMClient
# ======================================================================

from __future__ import annotations

from app.common.config import settings as _settings
from app.modules.agent.llm.llm_client import LLMClient


# URL por defecto de cada provider OpenAI-compatible (distinto de OpenAI)
_PROVIDER_BASE_URLS: dict[str, str] = {
    "xai":      "https://api.x.ai/v1",
    "deepseek": "https://api.deepseek.com",
    "gemini":   "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama":   "http://localhost:11434/v1",
}


class LLMClientFactory:
    """
    Factory para instanciar el cliente LLM según la configuración.

    Uso:
        client = LLMClientFactory.create()
        response = client.complete(system_prompt, user_message)
    """

    @staticmethod
    def create(settings=None) -> LLMClient:
        """
        Crea y retorna el cliente LLM configurado en settings.

        Args:
            settings: instancia de Settings (usa la global por defecto).
                      Inyectable en tests para usar distintas configs.

        Returns:
            LLMClient listo para usar.

        Raises:
            ValueError: si el provider configurado no es reconocido.
        """
        cfg = settings or _settings
        provider = cfg.LLM_PROVIDER.lower()

        if provider == "anthropic":
            from app.modules.agent.llm.anthropic_client import AnthropicLLMClient

            return AnthropicLLMClient(
                api_key=cfg.LLM_API_KEY,
                model=cfg.LLM_MODEL,
                temperature=cfg.LLM_TEMPERATURE,
                max_tokens=cfg.LLM_MAX_TOKENS,
            )

        # ------------------------------------------------------------------
        # Todos los demás providers son OpenAI-compatible
        # ------------------------------------------------------------------
        if provider not in ("openai", "xai", "deepseek", "gemini", "ollama"):
            raise ValueError(
                f"Provider LLM no reconocido: '{provider}'. "
                "Valores válidos: openai, anthropic, gemini, xai, deepseek, ollama"
            )

        from app.modules.agent.llm.openai_compatible_client import OpenAICompatibleClient

        # Prioridad de base_url:
        # 1) LLM_BASE_URL en settings (override manual)
        # 2) URL por defecto del provider (en _PROVIDER_BASE_URLS)
        # 3) None → openai usa su URL interna
        base_url = cfg.LLM_BASE_URL or _PROVIDER_BASE_URLS.get(provider)

        # Ollama no requiere api_key real — usa "ollama" como placeholder
        api_key = cfg.LLM_API_KEY or ("ollama" if provider == "ollama" else "")

        return OpenAICompatibleClient(
            api_key=api_key,
            model=cfg.LLM_MODEL,
            provider_name=provider,
            base_url=base_url,
            temperature=cfg.LLM_TEMPERATURE,
            max_tokens=cfg.LLM_MAX_TOKENS,
        )
