# -*- coding: utf-8 -*-

# ======================================================================
# app/common/contracts/transactional_repository.py
#
# PROPÓSITO:
# - Contrato común de todos los repositorios de dominio: confirmar o
#   descartar la unidad de trabajo en curso.
#
# REGLA:
# - `session.commit()` solo existe dentro de la capa repositorio.
# - El servicio decide CUÁNDO confirmar (al final del caso de uso) llamando
#   `self._repo.commit()`. Como todos los repositorios de un request
#   comparten la misma sesión, un commit confirma todas las escrituras del
#   caso de uso de forma atómica.
# ======================================================================

from __future__ import annotations

from typing import Protocol


class TransactionalRepository(Protocol):
    """Operaciones transaccionales que expone todo repositorio."""

    def commit(self) -> None:
        """Confirma todas las escrituras pendientes de la sesión."""
        ...

    def rollback(self) -> None:
        """Descarta todas las escrituras pendientes de la sesión."""
        ...
