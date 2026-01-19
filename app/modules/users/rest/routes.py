from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.users.services.app_meta_service import AppMetaService
from app.modules.users.rest.schemas import SuccessEnvelope

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/{meta_id}", response_model=SuccessEnvelope)
def get_meta(meta_id: int, db: Session = Depends(get_db)):
    service = AppMetaService(db)
    result = service.get_meta(meta_id)

    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)

    # 👇 IMPORTANTE: aquí devolvemos el envelope que el schema espera
    return {"success": True, "data": result.data}