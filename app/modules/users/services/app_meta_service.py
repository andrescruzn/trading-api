from sqlalchemy.orm import Session

from app.common.service_result import ServiceResult
from app.modules.users.infrastructure.repository import AppMetaRepository


class AppMetaService:
    """
    Capa de aplicación: reglas + validaciones.
    Devuelve ServiceResult (ok/fail) y NO HTTP.
    """

    def __init__(self, db: Session):
        self._repo = AppMetaRepository(db)

    def get_meta(self, meta_id: int) -> ServiceResult[dict]:
        if meta_id <= 0:
            return ServiceResult.fail("meta_id inválido")

        row = self._repo.get_by_id(meta_id)
        if not row:
            return ServiceResult.fail("Registro no encontrado")

        return ServiceResult.ok(
            {
                "id": row.id,
                "meta_key": row.meta_key,
                "meta_value": row.meta_value,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )