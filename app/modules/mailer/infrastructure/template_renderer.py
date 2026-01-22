# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/mailer/infrastructure/template_renderer.py
#
# PROPÓSITO:
# - Implementación concreta de TemplateRenderer usando Jinja2.
#
# POR QUÉ:
# - Jinja2 permite herencia de templates (base.html) y variables.
#
# NOTA:
# - Infrastructure sí puede depender de librerías externas.
# ======================================================================

from __future__ import annotations

import os
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.modules.mailer.domain.mail_contracts import TemplateRenderer


class JinjaTemplateRenderer(TemplateRenderer):
    """
    Renderizador Jinja2 basado en filesystem.

    Decisión:
    - Ubicamos templates junto al módulo (Screaming Architecture).
    """

    def __init__(self) -> None:
        # --------------------------------------------------------------
        # 1) Resolver ruta absoluta de /templates del módulo
        # --------------------------------------------------------------
        current_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.normpath(os.path.join(current_dir, "..", "templates"))

        # --------------------------------------------------------------
        # 2) Configurar motor Jinja
        # --------------------------------------------------------------
        self._env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template_filename: str, context: Dict[str, Any]) -> str:
        """
        Renderiza HTML desde un template.

        - template_filename: ej. "welcome.html"
        - context: variables para el template
        """
        template = self._env.get_template(template_filename)
        return template.render(**context)