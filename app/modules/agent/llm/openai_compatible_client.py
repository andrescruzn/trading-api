# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/openai_compatible_client.py
#
# Cliente LLM para providers que implementan la API de OpenAI.
#
# PROVIDERS SOPORTADOS:
#   openai   → base_url=None (usa https://api.openai.com/v1 por defecto)
#   xai      → base_url="https://api.x.ai/v1"
#   deepseek → base_url="https://api.deepseek.com"
#   gemini   → base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
#   ollama   → base_url="http://localhost:11434/v1", api_key="ollama"
#
# VENTAJA: Un único cliente cubre 5 de los 6 providers soportados.
# ======================================================================

from __future__ import annotations

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient


class OpenAICompatibleClient(LLMClient):
    """
    Cliente LLM para cualquier provider con API compatible con OpenAI.

    Usa la librería `openai` con una base_url configurable.
    Para Ollama (local), la api_key puede ser cualquier string no vacío.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        provider_name: str,
        base_url: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self._model = model
        self._provider_name = provider_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = self._build_client(api_key=api_key, base_url=base_url)

    @staticmethod
    def _build_client(api_key: str, base_url: str | None):
        """
        Instancia el cliente openai con la configuración del provider.

        Importación tardía (lazy import) para evitar fallar en startup
        si el paquete `openai` no está instalado.
        """
        try:
            from openai import OpenAI  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'openai' no está instalado. "
                "Ejecuta: pip install openai"
            ) from exc

        return OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Envía el prompt al LLM y retorna la respuesta cruda.

        Estructura de mensajes:
        - system: Prompt Maestro con instrucciones del agente
        - user:   Contexto de mercado construido dinámicamente

        Raises:
            LLMCallError: si el provider responde con error o timeout.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
        except Exception as exc:
            raise LLMCallError(
                provider=self._provider_name,
                detail=str(exc),
            ) from exc

        if not response.choices:
            raise LLMCallError(provider=self._provider_name, detail="empty choices in response")
        return response.choices[0].message.content or ""
