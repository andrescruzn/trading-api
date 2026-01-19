import os
from dotenv import load_dotenv

# Carga variables del .env en la raíz del proyecto
load_dotenv()

def get_database_url() -> str:
    """
    Construye la URL de conexión para SQLAlchemy (MySQL + PyMySQL).
    Se arma desde variables de entorno para que el proyecto quede portable.
    """
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")

    # driver: mysql+pymysql (SYNC)
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"