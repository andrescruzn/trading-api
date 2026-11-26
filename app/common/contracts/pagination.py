# -*- coding: utf-8 -*-

# ======================================================================
# app/common/contracts/pagination.py
#
# PROPÓSITO:
# - Contrato de paginación en el servidor, compartido por domain, services y REST.
#
# - PageRequest: qué página se pide (1-based) y su tamaño, ya acotados.
# - Page[T]: una página de resultados + el total de filas que cumplen los filtros.
#
# La capa REST la convierte con `build_paginated_response(items, total, page,
# page_size)` → `data: {items, pagination: {total, page, page_size, total_pages}}`.
# ======================================================================

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageRequest:
    """
    Página pedida por el cliente.

    `of()` acota los valores (página ≥ 1, tamaño 1–MAX_PAGE_SIZE) para que un
    servicio nunca lance un OFFSET negativo ni un LIMIT enorme, aunque la ruta
    ya los valide con `Query(ge=..., le=...)`.
    """
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def of(cls, page: int | None, page_size: int | None) -> PageRequest:
        safe_page = max(int(page if page is not None else 1), 1)
        size = page_size if page_size is not None else DEFAULT_PAGE_SIZE
        safe_size = min(max(int(size), 1), MAX_PAGE_SIZE)
        return cls(page=safe_page, page_size=safe_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass(frozen=True)
class Page(Generic[T]):
    """Una página de resultados. `total` cuenta todas las filas, no solo las de la página."""
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size if self.page_size > 0 else 0

    @classmethod
    def empty(cls, request: PageRequest) -> Page[T]:
        return cls(items=[], total=0, page=request.page, page_size=request.page_size)

    def map(self, fn: Callable[[T], U]) -> Page[U]:
        """Misma página con cada item transformado (p. ej. entidad → dict en REST)."""
        return Page(
            items=[fn(item) for item in self.items],
            total=self.total,
            page=self.page,
            page_size=self.page_size,
        )
