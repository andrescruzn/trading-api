# -*- coding: utf-8 -*-

# ======================================================================
# app/extensions/db/config.py
#
# RESPONSABILIDAD:
# - Construir la URL de conexión a la base de datos.
#
# NOTA ARQUITECTÓNICA:
# - NO carga variables de entorno.
# - NO usa dotenv.
# - Consume configuración ya resuelta desde app.common.config.
# ======================================================================

from app.common.config import settings


def get_database_url() -> str:
    """
    Construye la URL de conexión para SQLAlchemy (MySQL + PyMySQL).

    Decisión:
    - La configuración viene centralizada desde `settings`.
    - Esto mantiene a `extensions/db` desacoplado de cómo se cargan los envs.
    """
    return (
        f"mysql+pymysql://{settings.DB_USER}:"
        f"{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:"
        f"{settings.DB_PORT}/"
        f"{settings.DB_NAME}?charset=utf8mb4"
    )