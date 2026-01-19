from datetime import datetime
from pydantic import BaseModel


class AppMetaResponse(BaseModel):
    id: int
    meta_key: str | None
    meta_value: str | None
    created_at: datetime


class SuccessEnvelope(BaseModel):
    success: bool
    data: AppMetaResponse