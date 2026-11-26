# app/common/security/sanitization/__init__.py
# -*- coding: utf-8 -*-
from .html_sanitizer import sanitize_html

__all__ = ["sanitize_html"]