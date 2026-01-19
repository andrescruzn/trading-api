from sqlalchemy.orm import Session

from app.modules.users.domain.app_meta_model import AppMeta


class AppMetaRepository:
    """
    Infraestructura: solo queries SQLAlchemy.
    """

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, meta_id: int) -> AppMeta | None:
        return self._db.get(AppMeta, meta_id)