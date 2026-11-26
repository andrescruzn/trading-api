# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/gemini_client.py
#
# Cliente LLM para Gemini (Google AI Studio) con su SDK oficial
# (`google-genai`).
#
# NOTAS:
# - El Prompt Maestro va como `system_instruction`, no como mensaje.
# - El timeout del SDK va en milisegundos.
# - attempts=1: sin reintentos; el RotatingLLMClient hace el failover.
# ======================================================================

from __future__ import annotations

import time

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMCompletion, elapsed_ms

_PROVIDER = "gemini"


class GeminiLLMClient(LLMClient):
    """Cliente LLM para Gemini (generate_content)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = self._build_client(api_key=api_key, timeout=timeout)

    @staticmethod
    def _build_client(api_key: str, timeout: float):
        """Importación tardía: no falla en startup si falta el paquete."""
        try:
            from google import genai  # type: ignore[import]
            from google.genai import types  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'google-genai' no está instalado. Ejecuta: uv add google-genai"
            ) from exc

        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(timeout * 1000),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    def complete(self, system_prompt: str, user_message: str) -> LLMCompletion:
        """
        Raises:
            LLMCallError: si Gemini responde con error o timeout.
        """
        from google.genai import types  # type: ignore[import]

        started = time.perf_counter()
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self._temperature,
                    max_output_tokens=self._max_tokens,
                ),
            )
        except Exception as exc:
            raise LLMCallError(provider=_PROVIDER, detail=str(exc)) from exc

        # text es None si no hay partes de texto (p. ej. bloqueo por seguridad):
        # se devuelve vacío y AnalyzeService lo reporta como AGENT_LLM_PARSE_ERROR.
        return LLMCompletion(
            text=response.text or "",
            provider=_PROVIDER,
            model=self._model,
            latency_ms=elapsed_ms(started),
        )
