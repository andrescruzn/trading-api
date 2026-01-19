from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class AppMeta(Base):
    """
    Mapea la tabla app_meta.
    IMPORTANTE: reflejamos nombres tal cual en DB.
    """
    __tablename__ = "app_meta"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meta_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)