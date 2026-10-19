# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/rotating_client.py
#
# Cliente LLM que reparte las llamadas entre varios servicios (pool).
#
# DISEÑO:
# - Round-robin: cada llamada empieza en el servicio al que le toca el
#   turno, y el turno avanza uno por llamada.
# - Failover: si el servicio del turno falla (red, 429, 5xx, timeout),
#   se prueba el siguiente en la misma llamada. Solo si fallan todos se
#   lanza LLMCallError.
# - La latencia del LLMCompletion que devuelve es la de la consulta
#   completa (incluye los servicios que fallaron antes), y
#   failed_providers dice cuáles fueron.
# - El turno vive a nivel de módulo (por proceso): LLMClientFactory crea
#   un cliente por request, y los endpoints sync (threadpool) y el
#   scheduler comparten proceso, de ahí el lock.
# ======================================================================

from __future__ import annotations

import dataclasses
import logging
import threading
import time

from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMCompletion, elapsed_ms

logger = logging.getLogger(__name__)

_turn_lock = threading.Lock()
_turn = 0


def _next_start(size: int) -> int:
    """Devuelve el índice del servicio al que le toca y avanza el turno."""
    global _turn
    with _turn_lock:
        start = _turn % size
        _turn = (start + 1) % size
        return start


class RotatingLLMClient(LLMClient):
    """
    Pool de clientes LLM con rotación round-robin y failover.

    Args:
        services: lista ordenada de (nombre, cliente).
    """

    def __init__(self, services: list[tuple[str, LLMClient]]):
        self._services = services

    @property
    def service_names(self) -> list[str]:
        return [name for name, _ in self._services]

    def complete(self, system_prompt: str, user_message: str) -> LLMCompletion:
        if not self._services:
            raise LLMCallError(provider="pool", detail="no hay servicios LLM configurados")

        size = len(self._services)
        start = _next_start(size)
        failures: list[str] = []
        failed_providers: list[str] = []
        started = time.perf_counter()

        for offset in range(size):
            name, client = self._services[(start + offset) % size]
            try:
                response = client.complete(system_prompt=system_prompt, user_message=user_message)
            except LLMCallError as exc:
                logger.warning("[llm] %s falló, probando el siguiente: %s", name, exc.detail)
                failures.append(f"{name}: {exc.detail}")
                failed_providers.append(name)
                continue

            completion = dataclasses.replace(
                response,
                latency_ms=elapsed_ms(started),
                failed_providers=failed_providers,
            )
            logger.info(
                "[llm] respondió %s (%s) en %d ms",
                name, completion.model, completion.latency_ms,
            )
            return completion

        raise LLMCallError(provider="pool", detail="; ".join(failures))
