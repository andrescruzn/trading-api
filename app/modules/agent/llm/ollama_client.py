# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/ollama_client.py
#
# Cliente LLM para Ollama Cloud con su SDK oficial (`ollama`).
#
# NOTAS:
# - Host https://ollama.com con la API key como Bearer.
# - El modelo va con el nombre de https://ollama.com/api/tags, sin el
#   sufijo :cloud (ese solo lo usa la app/CLI local).
# - temperature y el tope de tokens (num_predict) van en `options`.
# - Si el modelo razona, el razonamiento llega aparte en message.thinking;
#   message.content trae solo la respuesta (el JSON).
# ======================================================================

from __future__ import annotations

import time

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMCompletion, elapsed_ms

_PROVIDER = "ollama"
_OLLAMA_CLOUD_HOST = "https://ollama.com"


class OllamaLLMClient(LLMClient):
    """Cliente LLM para Ollama Cloud (chat)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ):
        self._model = model
        self._options = {"temperature": temperature, "num_predict": max_tokens}
        self._client = self._build_client(api_key=api_key, timeout=timeout)

    @staticmethod
    def _build_client(api_key: str, timeout: float):
        """Importación tardía: no falla en startup si falta el paquete."""
        try:
            from ollama import Client  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'ollama' no está instalado. Ejecuta: uv add ollama"
            ) from exc

        return Client(
            host=_OLLAMA_CLOUD_HOST,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def complete(self, system_prompt: str, user_message: str) -> LLMCompletion:
        """
        Raises:
            LLMCallError: si Ollama responde con error o timeout.
        """
        started = time.perf_counter()
        try:
            response = self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                options=self._options,
            )
        except Exception as exc:
            raise LLMCallError(provider=_PROVIDER, detail=str(exc)) from exc

        return LLMCompletion(
            text=response.message.content or "",
            provider=_PROVIDER,
            model=self._model,
            latency_ms=elapsed_ms(started),
        )
