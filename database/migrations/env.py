# -*- coding: utf-8 -*-

# ======================================================================
# database/migrations/env.py
#
# PROPÓSITO:
# - Entorno de ejecución de Alembic: conecta con la BD y expone el
#   metadata de los modelos ORM para `revision --autogenerate`.
#
# DECISIONES:
# - Reutiliza `engine` de app.extensions.db: misma URL (settings/.env) y
#   mismo hook de `time_zone = '+00:00'` que la app.
# - Importa models_registry para que Base.metadata conozca TODAS las tablas.
# - `_include_object` ignora tablas que existen en la BD pero no tienen
#   modelo ORM (audit_logs, system_events, predictions, portfolio_snapshots,
#   http_audit_YYYY...). Sin esto, autogenerate propondría DROP TABLE.
# ======================================================================

from __future__ import annotations

from logging.config import fileConfig

from alembic import context

import app.extensions.db.models_registry  # noqa: F401  (registra los modelos en Base.metadata)
from app.extensions.db import Base, engine, get_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _include_object(obj, name, type_, reflected, compare_to) -> bool:
    """
    Filtro de autogenerate.

    Regla:
    - Una tabla que solo existe en la BD (reflected) y no tiene modelo
      (compare_to is None) se ignora: no está gestionada por el ORM.
    """
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    """Genera el SQL sin conectar a la BD (`alembic upgrade head --sql`)."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        include_object=_include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones contra la BD configurada en .env."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=_include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
