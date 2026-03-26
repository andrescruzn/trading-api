# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ListAlertEventsQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    from_ts: datetime | None = None
