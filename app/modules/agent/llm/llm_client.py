# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/llm_client.py
#
# Contrato (interfaz) para todos los clientes LLM.
#
# DISEÑO:
# - Un único método `complete` normaliza la interacción con cualquier LLM.
# - Recibe un system_prompt (instrucciones al modelo) y un user_message
#   (el contexto de mercado construido dinámicamente).
# - Retorna el texto crudo de la respuesta del LLM.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    Interfaz base para clientes de LLM.

    Implementaciones disponibles:
    - OpenAICompatibleClient  → openai, xai, deepseek, gemini, ollama
    - AnthropicLLMClient      → anthropic
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Llama al LLM y retorna la respuesta como texto.

        Args:
            system_prompt: instrucciones del sistema (Prompt Maestro).
            user_message: contexto de mercado + estrategia.

        Returns:
            Texto crudo de la respuesta del LLM.

        Raises:
            LLMCallError: si la llamada al provider falla.
            LLMParseError: si la respuesta no puede ser procesada.
        """
        ...


class LLMCallError(Exception):
    """Error al llamar al provider LLM (timeout, auth, red, etc.)."""

    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        super().__init__(f"[{provider}] LLM call failed: {detail}")


class LLMParseError(Exception):
    """Error al parsear la respuesta JSON del LLM."""

    def __init__(self, raw_response: str, detail: str):
        self.raw_response = raw_response
        self.detail = detail
        super().__init__(f"LLM parse error: {detail} | raw={raw_response[:200]}")
