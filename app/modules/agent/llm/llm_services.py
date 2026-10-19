# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/llm/llm_services.py
#
# Catálogo de servicios LLM que pueden entrar en el pool de rotación.
#
# DISEÑO:
# - Cada servicio usa el SDK oficial de su proveedor (un LLMClient por
#   servicio); todos comparten el constructor
#   (api_key, model, temperature, max_tokens, timeout).
# - La API key y el modelo se leen de settings (nombres de atributo),
#   nunca con os.getenv aquí.
# - Añadir un servicio = su cliente + una entrada aquí + sus dos
#   variables en settings.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.modules.agent.llm.gemini_client import GeminiLLMClient
from app.modules.agent.llm.groq_client import GroqLLMClient
from app.modules.agent.llm.llm_client import LLMClient
from app.modules.agent.llm.ollama_client import OllamaLLMClient


@dataclass(frozen=True)
class LLMServiceSpec:
    """Cómo construir el cliente de un servicio LLM del pool."""

    name: str
    client_cls: type[LLMClient]
    api_key_setting: str
    model_setting: str


LLM_SERVICE_CATALOG: dict[str, LLMServiceSpec] = {
    "groq": LLMServiceSpec(
        name="groq",
        client_cls=GroqLLMClient,
        api_key_setting="GROQ_API_KEY",
        model_setting="GROQ_MODEL",
    ),
    "gemini": LLMServiceSpec(
        name="gemini",
        client_cls=GeminiLLMClient,
        api_key_setting="GEMINI_API_KEY",
        model_setting="GEMINI_MODEL",
    ),
    "ollama": LLMServiceSpec(
        name="ollama",
        client_cls=OllamaLLMClient,
        api_key_setting="OLLAMA_API_KEY",
        model_setting="OLLAMA_MODEL",
    ),
}
