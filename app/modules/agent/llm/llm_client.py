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
# - Retorna un LLMCompletion: el texto crudo de la respuesta más qué
#   servicio y modelo respondieron y cuánto tardó la consulta.
# ======================================================================

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMCompletion:
    """Respuesta del LLM con los datos de la llamada (para auditoría)."""

    text: str                   # texto crudo de la respuesta
    provider: str               # servicio que respondió (groq, gemini, ollama)
    model: str                  # modelo que respondió
    latency_ms: int             # duración de la consulta en milisegundos
    failed_providers: list[str] = field(default_factory=list)  # servicios que fallaron antes (failover)


def elapsed_ms(started: float) -> int:
    """Milisegundos transcurridos desde `started` (valor de time.perf_counter())."""
    return round((time.perf_counter() - started) * 1000)


class LLMClient(ABC):
    """
    Interfaz base para clientes de LLM.

    Implementaciones disponibles:
    - GroqLLMClient / GeminiLLMClient / OllamaLLMClient → un servicio,
      cada uno con el SDK oficial de su proveedor
    - RotatingLLMClient       → pool de servicios con rotación y failover
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> LLMCompletion:
        """
        Llama al LLM y retorna la respuesta con los datos de la llamada.

        Args:
            system_prompt: instrucciones del sistema (Prompt Maestro).
            user_message: contexto de mercado + estrategia.

        Returns:
            LLMCompletion con el texto crudo, servicio, modelo y latencia.

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
