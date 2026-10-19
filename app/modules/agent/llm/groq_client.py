# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/groq_client.py
#
# Cliente LLM para Groq con su SDK oficial (`groq`).
#
# NOTA: max_retries=0 a propósito. Ante un fallo (p. ej. 429) el
# RotatingLLMClient pasa al siguiente servicio en vez de reintentar.
# ======================================================================

from __future__ import annotations

import time

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMCompletion, elapsed_ms

_PROVIDER = "groq"


class GroqLLMClient(LLMClient):
    """Cliente LLM para Groq (chat completions)."""

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
            from groq import Groq  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'groq' no está instalado. Ejecuta: uv add groq"
            ) from exc

        return Groq(api_key=api_key, timeout=timeout, max_retries=0)

    def complete(self, system_prompt: str, user_message: str) -> LLMCompletion:
        """
        Raises:
            LLMCallError: si Groq responde con error o timeout.
        """
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self._temperature,
                max_completion_tokens=self._max_tokens,
            )
        except Exception as exc:
            raise LLMCallError(provider=_PROVIDER, detail=str(exc)) from exc

        if not response.choices:
            raise LLMCallError(provider=_PROVIDER, detail="empty choices in response")
        return LLMCompletion(
            text=response.choices[0].message.content or "",
            provider=_PROVIDER,
            model=self._model,
            latency_ms=elapsed_ms(started),
        )
