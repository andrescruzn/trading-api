# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/anthropic_client.py
#
# Cliente LLM para Anthropic (Claude Opus, Sonnet, Haiku).
#
# DIFERENCIA CON OPENAI:
# - La Anthropic SDK separa el system prompt del array de messages.
# - El campo `system` va directamente en el payload (no como mensaje).
# - La respuesta se lee desde response.content[0].text (no .choices).
# ======================================================================

from __future__ import annotations

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient


class AnthropicLLMClient(LLMClient):
    """
    Cliente LLM para Anthropic (Claude 4 Opus, Sonnet, etc.).

    Requiere el paquete `anthropic` instalado:
        pip install anthropic
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = self._build_client(api_key=api_key)

    @staticmethod
    def _build_client(api_key: str):
        """Importación tardía para no fallar si `anthropic` no está instalado."""
        try:
            from anthropic import Anthropic  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'anthropic' no está instalado. "
                "Ejecuta: pip install anthropic"
            ) from exc
        return Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Envía el prompt a Claude y retorna la respuesta cruda.

        Raises:
            LLMCallError: si Anthropic responde con error o timeout.
        """
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                temperature=self._temperature,
            )
            return response.content[0].text
        except Exception as exc:
            raise LLMCallError(
                provider="anthropic",
                detail=str(exc),
            ) from exc
