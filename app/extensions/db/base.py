# app/extensions/db/base.py
# -*- coding: utf-8 -*-

from sqlalchemy.orm import DeclarativeBase

# Opciones de tabla MySQL comunes a todos los modelos. Van al final de
# `__table_args__` para que `alembic revision --autogenerate` genere las tablas
# con el mismo motor, charset y collation que el resto del esquema.
MYSQL_TABLE_OPTIONS: dict[str, str] = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


class Base(DeclarativeBase):
    """
    Base declarativa para todos los modelos SQLAlchemy.
    """
    pass
